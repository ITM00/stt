from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from app.utils.logger import get_logger

_LOGGER = get_logger(__name__)

_VK_CONTROL = 0x11
_VK_V = 0x56
_KEYEVENTF_KEYUP = 0x0002
_SW_RESTORE = 9


if sys.platform.startswith("win"):
    _USER32 = ctypes.windll.user32
else:
    _USER32 = None


class PasteManager:
    def __init__(self) -> None:
        self._target_hwnd: int | None = None

    def capture_recording_target(self) -> None:
        if _USER32 is None:
            self._target_hwnd = None
            return
        hwnd = int(_USER32.GetForegroundWindow())
        self._target_hwnd = hwnd if hwnd else None

    def paste_to_target_or_active(self) -> None:
        if _USER32 is None:
            return
        if self._target_hwnd and self._is_window(self._target_hwnd):
            self._try_focus_target(self._target_hwnd)
        self._send_ctrl_v()

    def _try_focus_target(self, hwnd: int) -> None:
        if _USER32.IsIconic(wintypes.HWND(hwnd)):
            _USER32.ShowWindow(wintypes.HWND(hwnd), _SW_RESTORE)
        try:
            _USER32.SetForegroundWindow(wintypes.HWND(hwnd))
        except Exception:
            _LOGGER.exception("Failed to focus captured target window")

    def _is_window(self, hwnd: int) -> bool:
        try:
            return bool(_USER32.IsWindow(wintypes.HWND(hwnd)))
        except Exception:
            return False

    def _send_ctrl_v(self) -> None:
        _USER32.keybd_event(_VK_CONTROL, 0, 0, 0)
        _USER32.keybd_event(_VK_V, 0, 0, 0)
        _USER32.keybd_event(_VK_V, 0, _KEYEVENTF_KEYUP, 0)
        _USER32.keybd_event(_VK_CONTROL, 0, _KEYEVENTF_KEYUP, 0)
