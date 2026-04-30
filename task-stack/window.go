package main

import (
	"fmt"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/widget"
)

var (
	taskList    *widget.List
	selectedIdx = -1
	selMu       sync.Mutex
)

func buildWindow(a fyne.App) fyne.Window {
	w := a.NewWindow("Task Stack")
	w.Resize(fyne.NewSize(480, 400))
	w.SetCloseIntercept(w.Hide)

	entry := widget.NewEntry()
	entry.SetPlaceHolder("New task...")

	taskList = widget.NewList(
		func() int {
			mu.Lock()
			defer mu.Unlock()
			return len(tasks)
		},
		func() fyne.CanvasObject {
			return container.NewHBox(
				widget.NewLabel("0"),
				widget.NewLabel("≡"),
				widget.NewLabel("●"),
				widget.NewLabel("task text here"),
				layout.NewSpacer(),
				widget.NewLabel("—"),
			)
		},
		func(id widget.ListItemID, item fyne.CanvasObject) {
			row := item.(*fyne.Container)
			mu.Lock()
			if int(id) >= len(tasks) {
				mu.Unlock()
				return
			}
			t := tasks[id]
			mu.Unlock()

			idxLabel := row.Objects[0].(*widget.Label)
			statusLabel := row.Objects[2].(*widget.Label)
			textLabel := row.Objects[3].(*widget.Label)
			tsLabel := row.Objects[5].(*widget.Label)

			idxLabel.SetText(fmt.Sprintf("%d", id))
			if id == 0 {
				statusLabel.SetText("●")
			} else {
				statusLabel.SetText("○")
			}
			textLabel.SetText(t.Text)
			if id == 0 {
				textLabel.TextStyle = fyne.TextStyle{Bold: true}
			} else {
				textLabel.TextStyle = fyne.TextStyle{}
			}
			textLabel.Refresh()
			tsLabel.SetText(FormatTimestamp(t.LastCurrent, time.Now()))
		},
	)

	taskList.OnSelected = func(id widget.ListItemID) {
		selMu.Lock()
		selectedIdx = int(id)
		selMu.Unlock()
	}

	entry.OnSubmitted = func(text string) {
		if text == "" {
			return
		}
		mu.Lock()
		tasks = Push(tasks, text)
		mu.Unlock()
		entry.SetText("")
		saveAndRefresh()
	}

	w.Canvas().SetOnTypedRune(func(r rune) {
		if w.Canvas().Focused() == entry {
			return
		}
		switch {
		case r == '/':
			selMu.Lock()
			idx := selectedIdx
			selMu.Unlock()
			if idx > 0 {
				mu.Lock()
				tasks = Promote(tasks, idx)
				mu.Unlock()
				selMu.Lock()
				selectedIdx = 0
				selMu.Unlock()
				taskList.Select(0)
				saveAndRefresh()
			}
		case r >= '0' && r <= '9':
			idx := int(r - '0')
			mu.Lock()
			n := len(tasks)
			mu.Unlock()
			if idx < n {
				selMu.Lock()
				selectedIdx = idx
				selMu.Unlock()
				taskList.Select(widget.ListItemID(idx))
			}
		}
	})

	w.Canvas().SetOnTypedKey(func(ke *fyne.KeyEvent) {
		if w.Canvas().Focused() == entry {
			return
		}
		switch ke.Name {
		case fyne.KeyBackspace, fyne.KeyDelete:
			selMu.Lock()
			idx := selectedIdx
			selMu.Unlock()
			if idx < 0 {
				return
			}
			mu.Lock()
			tasks = Remove(tasks, idx)
			n := len(tasks)
			mu.Unlock()
			newIdx := idx
			if newIdx >= n {
				newIdx = n - 1
			}
			selMu.Lock()
			selectedIdx = newIdx
			selMu.Unlock()
			if newIdx >= 0 {
				taskList.Select(widget.ListItemID(newIdx))
			} else {
				taskList.UnselectAll()
			}
			saveAndRefresh()
		case fyne.KeyEscape:
			w.Hide()
		}
	})

	content := container.NewBorder(entry, nil, nil, nil, taskList)
	w.SetContent(content)

	return w
}

func refreshList() {
	if taskList != nil {
		taskList.Refresh()
	}
}
