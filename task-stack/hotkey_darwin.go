//go:build darwin

package main

import "golang.design/x/hotkey"

var hotkeyMods = []hotkey.Modifier{hotkey.ModCmd, hotkey.ModShift}
