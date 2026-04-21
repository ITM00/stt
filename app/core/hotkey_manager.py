from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.utils.logger import get_logger


class HotkeyManager:
    def __init__(self, listener_factory: Callable[..., Any] | None = None) -> None:
        self._logger = get_logger(__name__)
        self._listener_factory = listener_factory or self._default_listener_factory
        self.listener: Any | None = None

    def _default_listener_factory(self, on_activate: Callable[[], None], hotkey: str) -> Any:
        from pynput import keyboard

        return keyboard.GlobalHotKeys({hotkey: on_activate})

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        self._logger.info("Registering hotkey: %s", hotkey)
        self.listener = self._listener_factory(callback, hotkey)
        self.listener.start()
        self._logger.info("Hotkey listener started")

    def stop(self) -> None:
        if self.listener is not None:
            self._logger.info("Stopping hotkey listener")
            self.listener.stop()
