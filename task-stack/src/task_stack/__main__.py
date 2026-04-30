from __future__ import annotations

import threading
import tkinter as tk

from .app import AppCoordinator, HotkeyListener, TrayApp
from .window import StackWindow


def main() -> None:
    root = tk.Tk()
    root.withdraw()  # hidden until opened

    coordinator: AppCoordinator | None = None

    def on_stack_change() -> None:
        if coordinator:
            coordinator.notify_stack_changed()

    win = StackWindow(root, on_stack_change=on_stack_change)

    coordinator = AppCoordinator(
        tk_after=root.after,
        window_show=win.show,
        window_refresh=win.refresh,
    )

    tray = TrayApp(
        on_open=coordinator.request_show,
        on_quit=root.quit,
    )
    coordinator.set_tray(tray)

    hotkey = HotkeyListener(callback=coordinator.request_show)
    hotkey.start()

    tray_thread = threading.Thread(target=tray.start, daemon=True, name="tray")
    tray_thread.start()

    try:
        root.mainloop()
    finally:
        tray.stop()
        hotkey.stop()


if __name__ == "__main__":
    main()
