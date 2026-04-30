package main

import (
	"log"
	"sync"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
)

var (
	mu        sync.Mutex
	tasks     []Task
	fyneApp   fyne.App
	fyneWin   fyne.Window
	showWinCh = make(chan struct{}, 1)
)

func main() {
	var err error
	tasks, err = Load()
	if err != nil {
		log.Printf("load: %v", err)
	}

	fyneApp = app.NewWithID("com.taskstack.app")
	fyneWin = buildWindow(fyneApp)

	setupTray()

	go startHotkey(showWinCh)
	go func() {
		for range showWinCh {
			fyne.Do(func() {
				fyneWin.Show()
				fyneWin.RequestFocus()
			})
		}
	}()

	fyneApp.Run()
}

func saveAndRefresh() {
	mu.Lock()
	t := make([]Task, len(tasks))
	copy(t, tasks)
	mu.Unlock()
	if err := Save(t); err != nil {
		log.Printf("save: %v", err)
	}
	updateTray(t)
	refreshList()
}
