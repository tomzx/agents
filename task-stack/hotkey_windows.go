//go:build windows

package main

import (
	"fmt"

	"golang.design/x/hotkey"
)

const hotkeyDefault = "ctrl+shift+t"

func modFromString(s string) (hotkey.Modifier, error) {
	switch s {
	case "ctrl":
		return hotkey.ModCtrl, nil
	case "shift":
		return hotkey.ModShift, nil
	case "alt":
		return hotkey.ModAlt, nil
	case "cmd", "win", "super":
		return hotkey.ModWin, nil
	}
	return 0, fmt.Errorf("unknown modifier %q — use ctrl, shift, alt, or cmd", s)
}
