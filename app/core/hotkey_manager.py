from __future__ import annotations

from collections.abc import Callable
from typing import Any


class HotkeyManager:
    def __init__(self, listener_factory: Callable[..., Any] | None = None) -> None:
        self._listener_factory = listener_factory or self._default_listener_factory
        self.listener: Any | None = None

    def _default_listener_factory(self, on_activate: Callable[[], None], hotkey: str) -> Any:
        from pynput import keyboard

        return keyboard.GlobalHotKeys({hotkey: on_activate})

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        self.listener = self._listener_factory(callback, hotkey)
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
