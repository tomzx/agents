package main

import (
	"log"
	"sync"

	"golang.design/x/hotkey"
)

var (
	hotkeyConfigCh = make(chan string, 1)
	hotkeyMu       sync.Mutex
	currentHK      *hotkey.Hotkey
	currentDoneCh  chan struct{}
)

// startHotkey registers the global hotkey from config and re-registers whenever
// hotkeyConfigCh receives a new shortcut string.
func startHotkey(notifyCh chan<- struct{}) {
	cfg := LoadConfig()
	applyHotkey(cfg.Hotkey, notifyCh)
	for newStr := range hotkeyConfigCh {
		applyHotkey(newStr, notifyCh)
	}
}

func applyHotkey(s string, notifyCh chan<- struct{}) {
	mods, key, err := parseHotkey(s)
	if err != nil {
		log.Printf("invalid hotkey %q: %v", s, err)
		return
	}

	// Stop previous listener goroutine and unregister old key.
	hotkeyMu.Lock()
	if currentDoneCh != nil {
		close(currentDoneCh)
		currentDoneCh = nil
	}
	if currentHK != nil {
		currentHK.Unregister()
		currentHK = nil
	}
	hotkeyMu.Unlock()

	hk := hotkey.New(mods, key)
	if err := hk.Register(); err != nil {
		log.Printf("hotkey register %q: %v", s, err)
		return
	}

	doneCh := make(chan struct{})
	hotkeyMu.Lock()
	currentHK = hk
	currentDoneCh = doneCh
	hotkeyMu.Unlock()

	go func() {
		for {
			select {
			case <-hk.Keydown():
				select {
				case notifyCh <- struct{}{}:
				default:
				}
			case <-doneCh:
				return
			}
		}
	}()
}
