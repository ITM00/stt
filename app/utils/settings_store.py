from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

_LOGGER = get_logger(__name__)
_SETTINGS_VERSION = 1
_APP_DIR_NAME = "stt-desktop"
_SETTINGS_FILENAME = "settings.json"


@dataclass(slots=True)
class UserSettings:
    silence_threshold_db: float = 30.0
    silence_timeout_seconds: float = 3.0
    record_toggle_hotkey: str = "<ctrl>+<shift>+a"
    auto_paste_enabled: bool = False


def _default_settings_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / _APP_DIR_NAME / _SETTINGS_FILENAME
    return Path.home() / ".config" / _APP_DIR_NAME / _SETTINGS_FILENAME


def _sanitize_payload(payload: dict[str, Any]) -> UserSettings:
    defaults = UserSettings()
    threshold = payload.get("silence_threshold_db", defaults.silence_threshold_db)
    timeout = payload.get("silence_timeout_seconds", defaults.silence_timeout_seconds)
    hotkey = payload.get("record_toggle_hotkey", defaults.record_toggle_hotkey)
    auto_paste_enabled = payload.get("auto_paste_enabled", defaults.auto_paste_enabled)
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        threshold = defaults.silence_threshold_db
    try:
        timeout = float(timeout)
    except (TypeError, ValueError):
        timeout = defaults.silence_timeout_seconds

    threshold = max(0.0, min(100.0, threshold))
    timeout = max(0.1, min(30.0, timeout))
    if not isinstance(hotkey, str):
        hotkey = defaults.record_toggle_hotkey
    hotkey = hotkey.strip()
    if not hotkey:
        hotkey = defaults.record_toggle_hotkey
    if not isinstance(auto_paste_enabled, bool):
        auto_paste_enabled = defaults.auto_paste_enabled
    return UserSettings(
        silence_threshold_db=threshold,
        silence_timeout_seconds=timeout,
        record_toggle_hotkey=hotkey,
        auto_paste_enabled=auto_paste_enabled,
    )


def load_user_settings(path: Path | None = None) -> UserSettings:
    settings_path = path or _default_settings_path()
    if not settings_path.exists():
        return UserSettings()
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _LOGGER.warning("Failed loading settings from %s; using defaults", settings_path)
        return UserSettings()
    if not isinstance(payload, dict):
        return UserSettings()
    return _sanitize_payload(payload)


def save_user_settings(settings: UserSettings, path: Path | None = None) -> None:
    settings_path = path or _default_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": _SETTINGS_VERSION, **asdict(settings)}
    settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def apply_user_settings(recorder: Any, settings: UserSettings) -> None:
    recorder.silence_threshold_db = settings.silence_threshold_db
    recorder.silence_timeout_seconds = settings.silence_timeout_seconds
