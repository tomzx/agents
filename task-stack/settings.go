package main

import (
	"fmt"
	"strings"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/widget"
)

func showSettings(parent fyne.Window) {
	cfg := LoadConfig()

	entry := widget.NewEntry()
	entry.SetText(cfg.Hotkey)
	entry.SetPlaceHolder("e.g. ctrl+shift+t")
	entry.Validator = func(s string) error {
		_, _, err := parseHotkey(strings.ToLower(strings.TrimSpace(s)))
		return err
	}

	hint := widget.NewLabel("Modifiers: ctrl  shift  alt  cmd\nKeys: a-z  0-9  f1-f12")
	hint.TextStyle = fyne.TextStyle{Italic: true}

	content := container.NewVBox(
		widget.NewForm(widget.NewFormItem("Global Shortcut", entry)),
		hint,
	)

	dialog.ShowCustomConfirm("Settings", "Save", "Cancel", content, func(ok bool) {
		if !ok {
			return
		}
		newVal := strings.ToLower(strings.TrimSpace(entry.Text))
		if _, _, err := parseHotkey(newVal); err != nil {
			dialog.ShowError(fmt.Errorf("invalid shortcut: %v", err), parent)
			return
		}
		cfg.Hotkey = newVal
		if err := SaveConfig(cfg); err != nil {
			dialog.ShowError(err, parent)
			return
		}
		select {
		case hotkeyConfigCh <- newVal:
		default:
		}
	}, parent)
}
