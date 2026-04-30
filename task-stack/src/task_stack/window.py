from __future__ import annotations

import tkinter as tk
from datetime import datetime, timezone
from typing import Callable

from . import stack as st


_FONT_CURRENT = ("TkDefaultFont", 11, "bold")
_FONT_NORMAL = ("TkDefaultFont", 11)
_COLOR_CURRENT_BG = "#e8f0fe"
_COLOR_SELECTED_BG = "#d0e4ff"
_COLOR_BG = "#ffffff"
_ROW_HEIGHT = 28


class StackWindow:
    def __init__(self, root: tk.Tk, on_stack_change: Callable[[], None]) -> None:
        self.root = root
        self.on_stack_change = on_stack_change
        self._tasks: list[st.Task] = []
        self._selected: int | None = None
        self._drag_start: int | None = None
        self._drag_y0: int = 0

        root.title("Task Stack")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.hide)
        root.bind("<Escape>", lambda _: self.hide())
        root.attributes("-topmost", True)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.root.configure(bg="#f0f0f0")
        pad = {"padx": 8, "pady": 6}

        top = tk.Frame(self.root, bg="#f0f0f0")
        top.pack(fill=tk.X, **pad)

        self._entry = tk.Entry(top, font=_FONT_NORMAL, relief=tk.FLAT, bg="white",
                               highlightthickness=1, highlightbackground="#aaa")
        self._entry.pack(fill=tk.X, ipady=4)
        self._entry.bind("<Return>", self._on_enter)

        self._canvas = tk.Canvas(self.root, bg=_COLOR_BG, highlightthickness=0,
                                 width=460, height=_ROW_HEIGHT)
        self._canvas.pack(fill=tk.BOTH, padx=8, pady=(0, 8))

        self._canvas.bind("<ButtonPress-1>", self._drag_press)
        self._canvas.bind("<B1-Motion>", self._drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._drag_release)
        self.root.bind("<Key>", self._on_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        self.refresh()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._entry.focus_set()

    def hide(self) -> None:
        self.root.withdraw()

    def refresh(self, tasks: list[st.Task] | None = None) -> None:
        if tasks is not None:
            self._tasks = tasks
        else:
            self._tasks = st.load()
        self._selected = None
        self._redraw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _redraw(self) -> None:
        c = self._canvas
        c.delete("all")
        count = len(self._tasks)
        height = max(count, 1) * _ROW_HEIGHT
        c.configure(height=height)
        now = datetime.now(tz=timezone.utc)

        for i, task in enumerate(self._tasks):
            y0 = i * _ROW_HEIGHT
            y1 = y0 + _ROW_HEIGHT

            if i == self._selected:
                bg = _COLOR_SELECTED_BG
            elif i == 0:
                bg = _COLOR_CURRENT_BG
            else:
                bg = _COLOR_BG

            c.create_rectangle(0, y0, 460, y1, fill=bg, outline="", tags=f"row{i}")

            # drag handle
            for dy in (8, 13, 18):
                c.create_line(8, y0 + dy, 18, y0 + dy, fill="#aaa", width=1.5)

            # index
            font = _FONT_CURRENT if i == 0 else _FONT_NORMAL
            c.create_text(26, y0 + _ROW_HEIGHT // 2, text=str(i), anchor=tk.W,
                          font=font, fill="#666")

            # indicator
            indicator = "●" if i == 0 else "○"
            c.create_text(44, y0 + _ROW_HEIGHT // 2, text=indicator, anchor=tk.W,
                          font=font, fill="#333")

            # task text (truncated)
            c.create_text(66, y0 + _ROW_HEIGHT // 2, text=task.text, anchor=tk.W,
                          font=font, fill="#111", width=290)

            # timestamp
            ts = st.format_timestamp(task.last_current, now)
            c.create_text(452, y0 + _ROW_HEIGHT // 2, text=ts, anchor=tk.E,
                          font=("TkFixedFont", 10), fill="#888")

        if not self._tasks:
            c.create_text(230, _ROW_HEIGHT // 2, text="No tasks — type above and press Enter",
                          fill="#aaa", font=_FONT_NORMAL)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _on_enter(self, _event: tk.Event) -> None:
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, tk.END)
        tasks = st.push(text)
        self._tasks = tasks
        self._selected = None
        self._redraw()
        self.on_stack_change()

    def _on_key(self, event: tk.Event) -> None:
        # Digit keys (main row and numpad) select a row
        if event.keysym.isdigit() or (event.keysym.startswith("KP_") and event.keysym[3:].isdigit()):
            if event.widget is self._entry:
                return
            digit = int(event.keysym[-1])
            if digit < len(self._tasks):
                self._selected = digit
                self._redraw()
            return

        if self._selected is None:
            return

        if event.keysym in ("slash", "KP_Divide"):
            tasks = st.promote(self._selected)
            self._tasks = tasks
            self._selected = None
            self._redraw()
            self.on_stack_change()

        elif event.keysym in ("BackSpace", "Delete"):
            tasks = st.remove(self._selected)
            self._tasks = tasks
            self._selected = None
            self._redraw()
            self.on_stack_change()

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------

    def _row_at(self, y: int) -> int:
        return max(0, min(len(self._tasks) - 1, y // _ROW_HEIGHT))

    def _drag_press(self, event: tk.Event) -> None:
        if not self._tasks:
            return
        self._drag_start = self._row_at(event.y)
        self._drag_y0 = event.y

    def _drag_motion(self, event: tk.Event) -> None:
        if self._drag_start is None or len(self._tasks) < 2:
            return
        target = self._row_at(event.y)
        if target != self._drag_start:
            self._tasks = st.reorder(self._drag_start, target)
            self._drag_start = target
            self._redraw()
            self.on_stack_change()

    def _drag_release(self, event: tk.Event) -> None:
        self._drag_start = None
