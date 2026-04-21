from __future__ import annotations

from collections.abc import Callable

import pyperclip


class ClipboardManager:
    def __init__(self, copy_fn: Callable[[str], None] | None = None) -> None:
        self._copy_fn = copy_fn or pyperclip.copy

    def copy_text(self, text: str) -> None:
        self._copy_fn(text)
