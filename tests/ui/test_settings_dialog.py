from app.ui.settings_dialog import SettingsDialog
from app.utils.settings_store import UserSettings
from PySide6.QtWidgets import QApplication


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_dialog_loads_initial_values() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(silence_threshold_db=31.0, silence_timeout_seconds=2.0))
    values = dialog.values()
    assert values.silence_threshold_db == 31.0
    assert values.silence_timeout_seconds == 2.0


def test_dialog_values_reflect_user_edits() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings())
    dialog._widgets["silence_threshold_db"].setValue(45.0)
    dialog._widgets["silence_timeout_seconds"].setValue(1.75)
    values = dialog.values()
    assert values.silence_threshold_db == 45.0
    assert values.silence_timeout_seconds == 1.75
