from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

STACK_FILE = Path.home() / ".task-stack.json"
_TMP = STACK_FILE.with_suffix(".json.tmp")


@dataclass
class Task:
    text: str
    last_current: datetime | None = field(default=None)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "last_current": self.last_current.isoformat() if self.last_current else None,
        }

    @staticmethod
    def from_dict(d: dict) -> "Task":
        lc = d.get("last_current")
        return Task(
            text=d["text"],
            last_current=datetime.fromisoformat(lc) if lc else None,
        )


def load() -> list[Task]:
    if not STACK_FILE.exists():
        return []
    try:
        data = json.loads(STACK_FILE.read_text())
        return [Task.from_dict(item) for item in data]
    except Exception:
        return []


def save(tasks: list[Task]) -> None:
    data = json.dumps([t.to_dict() for t in tasks], indent=2)
    _TMP.write_text(data)
    os.replace(_TMP, STACK_FILE)


def push(text: str) -> list[Task]:
    tasks = load()
    task = Task(text=text.strip(), last_current=datetime.now(tz=timezone.utc))
    tasks.insert(0, task)
    save(tasks)
    return tasks


def pop() -> tuple[Task | None, list[Task]]:
    tasks = load()
    if not tasks:
        return None, []
    removed = tasks.pop(0)
    if tasks:
        tasks[0].last_current = datetime.now(tz=timezone.utc)
    save(tasks)
    return removed, tasks


def reorder(from_idx: int, to_idx: int) -> list[Task]:
    tasks = load()
    if from_idx == to_idx or not (0 <= from_idx < len(tasks)) or not (0 <= to_idx < len(tasks)):
        return tasks
    task = tasks.pop(from_idx)
    tasks.insert(to_idx, task)
    if to_idx == 0:
        tasks[0].last_current = datetime.now(tz=timezone.utc)
    save(tasks)
    return tasks


def promote(idx: int) -> list[Task]:
    return reorder(idx, 0)


def remove(idx: int) -> list[Task]:
    tasks = load()
    if not (0 <= idx < len(tasks)):
        return tasks
    tasks.pop(idx)
    if tasks and idx == 0:
        tasks[0].last_current = datetime.now(tz=timezone.utc)
    save(tasks)
    return tasks


def format_timestamp(dt: datetime | None, now: datetime | None = None) -> str:
    if dt is None:
        return "—"
    if now is None:
        now = datetime.now(tz=timezone.utc)
    # Normalize both to UTC-aware for comparison
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if dt.year != now.year:
        return dt.strftime("%Y-%m-%d %H:%M")
    if dt.month != now.month:
        return dt.strftime("%m-%d %H:%M")
    if dt.day != now.day:
        return dt.strftime("%d %H:%M")
    if dt.hour != now.hour:
        return dt.strftime("%H:%M")
    return dt.strftime("%M")
