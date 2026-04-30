package main

import (
	"log"

	"golang.design/x/hotkey"
)

func startHotkey(ch chan<- struct{}) {
	hk := hotkey.New(hotkeyMods, hotkey.KeyT)
	if err := hk.Register(); err != nil {
		log.Printf("hotkey register: %v", err)
		return
	}
	defer hk.Unregister()
	for range hk.Keydown() {
		select {
		case ch <- struct{}{}:
		default:
		}
	}
}
