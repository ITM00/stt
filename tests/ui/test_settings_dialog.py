from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.ui.settings_dialog import SettingsDialog
from app.utils.settings_store import UserSettings


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_dialog_loads_initial_values() -> None:
    _ensure_app()
    dialog = SettingsDialog(
        UserSettings(
            silence_threshold_db=31.0,
            silence_timeout_seconds=2.0,
            record_toggle_hotkey="ctrl+shift+z",
        )
    )
    values = dialog.values()
    assert values.silence_threshold_db == 31.0
    assert values.silence_timeout_seconds == 2.0
    assert values.record_toggle_hotkey == "ctrl+shift+z"


def test_dialog_values_reflect_user_edits() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings())
    dialog._widgets["silence_threshold_db"].setValue(45.0)
    dialog._widgets["silence_timeout_seconds"].setValue(1.75)
    dialog._hotkey_input.setText("alt+space")
    values = dialog.values()
    assert values.silence_threshold_db == 45.0
    assert values.silence_timeout_seconds == 1.75
    assert values.record_toggle_hotkey == "alt+space"


def test_hotkey_input_captures_and_rewrites_combo() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(record_toggle_hotkey="Ctrl+Shift+A"))

    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_R,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        "r",
    )
    dialog._hotkey_input.keyPressEvent(event)
    assert dialog.values().record_toggle_hotkey == "Ctrl+Shift+R"


def test_hotkey_input_captures_win_modifier_combo() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(record_toggle_hotkey="Ctrl+Shift+A"))

    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_R,
        Qt.KeyboardModifier.MetaModifier,
        "r",
    )
    dialog._hotkey_input.keyPressEvent(event)
    assert dialog.values().record_toggle_hotkey == "Win+R"


def test_hotkey_input_captures_win_when_ctrl_pressed_first() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(record_toggle_hotkey="Ctrl+Shift+A"))

    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Meta,
        Qt.KeyboardModifier.ControlModifier,
        "",
    )
    dialog._hotkey_input.keyPressEvent(event)
    assert dialog.values().record_toggle_hotkey == "Ctrl+Win"


def test_hotkey_input_uses_native_vk_for_win_ctrl_letter_combo() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(record_toggle_hotkey="Ctrl+Shift+A"))

    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_unknown,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier,
        0,
        0x46,
        0,
        "",
        False,
        1,
    )
    dialog._hotkey_input.keyPressEvent(event)
    assert dialog.values().record_toggle_hotkey == "Ctrl+Win+F"


def test_hotkey_input_uses_qt_letter_key_when_text_is_empty() -> None:
    _ensure_app()
    dialog = SettingsDialog(UserSettings(record_toggle_hotkey="Ctrl+Shift+A"))

    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_F,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        "",
    )
    dialog._hotkey_input.keyPressEvent(event)
    assert dialog.values().record_toggle_hotkey == "Ctrl+Shift+F"
