package main

import "fyne.io/fyne/v2"

// trayApp is a local duck-type interface matching the concrete fyne app methods
// for system tray support (present on desktop platforms).
type trayApp interface {
	SetSystemTrayMenu(*fyne.Menu)
	SetSystemTrayIcon(fyne.Resource)
	SetSystemTrayWindow(fyne.Window)
}

func setupTray() {
	ta, ok := fyneApp.(trayApp)
	if !ok {
		return
	}
	ta.SetSystemTrayWindow(fyneWin)
	updateTray(tasks)
}

func updateTray(t []Task) {
	ta, ok := fyneApp.(trayApp)
	if !ok {
		return
	}

	label := "No tasks"
	if len(t) > 0 {
		label = t[0].Text
	}

	items := []*fyne.MenuItem{
		{Label: label, Disabled: true},
		fyne.NewMenuItemSeparator(),
		fyne.NewMenuItem("Open Stack", func() {
			fyneWin.Show()
			fyneWin.RequestFocus()
		}),
	}

	if len(t) > 0 {
		items = append(items, fyne.NewMenuItem("Mark Done", func() {
			mu.Lock()
			tasks, _ = Pop(tasks)
			mu.Unlock()
			saveAndRefresh()
		}))
	}

	items = append(items,
		fyne.NewMenuItemSeparator(),
		fyne.NewMenuItem("Settings", func() {
			fyneWin.Show()
			showSettings(fyneWin)
		}),
		fyne.NewMenuItem("Quit", func() { fyneApp.Quit() }),
	)

	ta.SetSystemTrayMenu(fyne.NewMenu("", items...))
	ta.SetSystemTrayIcon(makeIconFyne(len(t) > 0))
}
