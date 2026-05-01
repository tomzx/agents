//go:build !darwin && !windows

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
		return hotkey.Mod1, nil
	case "cmd", "super", "win":
		return hotkey.Mod4, nil
	}
	return 0, fmt.Errorf("unknown modifier %q — use ctrl, shift, alt, or cmd", s)
}
