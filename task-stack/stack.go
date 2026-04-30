package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

type Task struct {
	Text        string     `json:"text"`
	LastCurrent *time.Time `json:"last_current"`
}

func stackPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".task-stack.json")
}

func Load() ([]Task, error) {
	data, err := os.ReadFile(stackPath())
	if os.IsNotExist(err) {
		return []Task{}, nil
	}
	if err != nil {
		return nil, err
	}
	var tasks []Task
	if err := json.Unmarshal(data, &tasks); err != nil {
		return nil, err
	}
	return tasks, nil
}

func Save(tasks []Task) error {
	data, err := json.MarshalIndent(tasks, "", "  ")
	if err != nil {
		return err
	}
	tmp := stackPath() + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, stackPath())
}

func Push(tasks []Task, text string) []Task {
	now := time.Now().UTC()
	return append([]Task{{Text: text, LastCurrent: &now}}, tasks...)
}

func Pop(tasks []Task) ([]Task, *Task) {
	if len(tasks) == 0 {
		return tasks, nil
	}
	t := tasks[0]
	return tasks[1:], &t
}

func Promote(tasks []Task, idx int) []Task {
	if idx <= 0 || idx >= len(tasks) {
		return tasks
	}
	now := time.Now().UTC()
	promoted := tasks[idx]
	promoted.LastCurrent = &now
	result := make([]Task, 0, len(tasks))
	result = append(result, promoted)
	result = append(result, tasks[:idx]...)
	return append(result, tasks[idx+1:]...)
}

func Remove(tasks []Task, idx int) []Task {
	if idx < 0 || idx >= len(tasks) {
		return tasks
	}
	result := make([]Task, 0, len(tasks)-1)
	result = append(result, tasks[:idx]...)
	return append(result, tasks[idx+1:]...)
}

func FormatTimestamp(t *time.Time, now time.Time) string {
	if t == nil {
		return "—"
	}
	l := t.Local()
	n := now.Local()
	switch {
	case l.Year() != n.Year():
		return l.Format("2006-01-02 15:04")
	case l.Month() != n.Month():
		return l.Format("01-02 15:04")
	case l.Day() != n.Day():
		return l.Format("02 15:04")
	case l.Hour() != n.Hour():
		return l.Format("15:04")
	default:
		return l.Format("04")
	}
}
