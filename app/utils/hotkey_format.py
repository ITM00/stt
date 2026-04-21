from __future__ import annotations


def as_pynput_global_hotkey(hotkey: str) -> str:
    """Convert human-friendly hotkey strings into pynput GlobalHotKeys keys.

    pynput requires special keys to be wrapped in angle brackets, e.g. ``<space>``.
    Modifiers are typically written as ``<ctrl>``, ``<shift>``, ``<alt>``.
    """

    parts = [part.strip() for part in hotkey.split("+") if part.strip()]
    normalized: list[str] = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            normalized.append(part)
            continue

        lower = part.lower()
        if lower in {"ctrl", "control"}:
            normalized.append("<ctrl>")
            continue
        if lower in {"shift"}:
            normalized.append("<shift>")
            continue
        if lower in {"alt"}:
            normalized.append("<alt>")
            continue

        if len(part) == 1 and part.isalpha():
            normalized.append(part.lower())
            continue

        normalized.append(f"<{lower}>")

    return "+".join(normalized)
