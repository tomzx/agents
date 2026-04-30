from __future__ import annotations

import platform
import queue
import threading
from typing import Callable

import pystray
from pynput import keyboard

from . import stack as st
from .icon import make_icon


class TrayApp:
    def __init__(self, on_open: Callable[[], None], on_quit: Callable[[], None]) -> None:
        self._on_open = on_open
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None

    def start(self) -> None:
        tasks = st.load()
        image = make_icon(len(tasks))
        current_text = tasks[0].text if tasks else "No tasks"

        self._icon = pystray.Icon(
            "task-stack",
            image,
            title=current_text,
            menu=self._build_menu(tasks),
        )
        self._icon.run()  # blocks — must be called from its own thread

    def update(self, tasks: list[st.Task]) -> None:
        if self._icon is None:
            return
        self._icon.icon = make_icon(len(tasks))
        self._icon.title = tasks[0].text if tasks else "No tasks"
        self._icon.menu = self._build_menu(tasks)

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    # ------------------------------------------------------------------

    def _build_menu(self, tasks: list[st.Task]) -> pystray.Menu:
        current_label = tasks[0].text if tasks else "No tasks"
        items = [
            pystray.MenuItem(current_label, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Stack", lambda icon, item: self._on_open()),
            pystray.MenuItem(
                "Mark Done (pop)",
                lambda icon, item: self._pop_and_update(),
                enabled=bool(tasks),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda icon, item: self._on_quit()),
        ]
        return pystray.Menu(*items)

    def _pop_and_update(self) -> None:
        _, tasks = st.pop()
        self.update(tasks)


class HotkeyListener:
    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        system = platform.system()
        if system == "Darwin":
            hotkey = "<cmd>+<shift>+t"
        else:
            hotkey = "<ctrl>+<shift>+t"

        self._listener = keyboard.GlobalHotKeys({hotkey: self._callback})
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()


class AppCoordinator:
    """Wires together the tray, hotkey listener, and tkinter window via a thread-safe queue."""

    def __init__(self, tk_after: Callable, window_show: Callable, window_refresh: Callable) -> None:
        self._tk_after = tk_after
        self._window_show = window_show
        self._window_refresh = window_refresh
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._tray: TrayApp | None = None

    def set_tray(self, tray: TrayApp) -> None:
        self._tray = tray

    def request_show(self) -> None:
        self._queue.put("show")
        self._tk_after(0, self._drain)

    def notify_stack_changed(self) -> None:
        tasks = st.load()
        if self._tray:
            self._tray.update(tasks)

    def _drain(self) -> None:
        while not self._queue.empty():
            msg = self._queue.get_nowait()
            if msg == "show":
                self._window_refresh()
                self._window_show()
