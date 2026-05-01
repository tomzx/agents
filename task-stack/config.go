package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"golang.design/x/hotkey"
)

type Config struct {
	Hotkey string `json:"hotkey"`
}

func configPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".task-stack-config.json")
}

func LoadConfig() Config {
	data, err := os.ReadFile(configPath())
	if err != nil {
		return Config{Hotkey: hotkeyDefault}
	}
	var c Config
	if err := json.Unmarshal(data, &c); err != nil || c.Hotkey == "" {
		return Config{Hotkey: hotkeyDefault}
	}
	return c
}

func SaveConfig(c Config) error {
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	tmp := configPath() + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, configPath())
}

// parseHotkey parses a string like "ctrl+shift+t" or "cmd+shift+t" into modifiers and key.
func parseHotkey(s string) ([]hotkey.Modifier, hotkey.Key, error) {
	parts := strings.Split(strings.ToLower(strings.TrimSpace(s)), "+")
	if len(parts) < 2 {
		return nil, 0, fmt.Errorf("must have at least one modifier and a key, e.g. ctrl+shift+t")
	}
	var mods []hotkey.Modifier
	for _, p := range parts[:len(parts)-1] {
		m, err := modFromString(p)
		if err != nil {
			return nil, 0, err
		}
		mods = append(mods, m)
	}
	key, err := keyFromString(parts[len(parts)-1])
	if err != nil {
		return nil, 0, err
	}
	return mods, key, nil
}

func keyFromString(s string) (hotkey.Key, error) {
	if len(s) == 1 {
		switch {
		case s[0] >= 'a' && s[0] <= 'z':
			letters := []hotkey.Key{
				hotkey.KeyA, hotkey.KeyB, hotkey.KeyC, hotkey.KeyD, hotkey.KeyE,
				hotkey.KeyF, hotkey.KeyG, hotkey.KeyH, hotkey.KeyI, hotkey.KeyJ,
				hotkey.KeyK, hotkey.KeyL, hotkey.KeyM, hotkey.KeyN, hotkey.KeyO,
				hotkey.KeyP, hotkey.KeyQ, hotkey.KeyR, hotkey.KeyS, hotkey.KeyT,
				hotkey.KeyU, hotkey.KeyV, hotkey.KeyW, hotkey.KeyX, hotkey.KeyY,
				hotkey.KeyZ,
			}
			return letters[s[0]-'a'], nil
		case s[0] >= '0' && s[0] <= '9':
			digits := []hotkey.Key{
				hotkey.Key0, hotkey.Key1, hotkey.Key2, hotkey.Key3, hotkey.Key4,
				hotkey.Key5, hotkey.Key6, hotkey.Key7, hotkey.Key8, hotkey.Key9,
			}
			return digits[s[0]-'0'], nil
		}
	}
	fkeys := map[string]hotkey.Key{
		"f1": hotkey.KeyF1, "f2": hotkey.KeyF2, "f3": hotkey.KeyF3,
		"f4": hotkey.KeyF4, "f5": hotkey.KeyF5, "f6": hotkey.KeyF6,
		"f7": hotkey.KeyF7, "f8": hotkey.KeyF8, "f9": hotkey.KeyF9,
		"f10": hotkey.KeyF10, "f11": hotkey.KeyF11, "f12": hotkey.KeyF12,
	}
	if k, ok := fkeys[s]; ok {
		return k, nil
	}
	return 0, fmt.Errorf("unknown key %q — use a-z, 0-9, or f1-f12", s)
}
