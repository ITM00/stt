from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.settings_store import UserSettings


@dataclass(frozen=True, slots=True)
class _FieldDescriptor:
    key: str
    label: str
    minimum: float
    maximum: float
    step: float
    decimals: int


class HotkeyCaptureLineEdit(QLineEdit):
    _MODIFIER_KEYS = {
        Qt.Key.Key_Control,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Meta,
        Qt.Key.Key_Super_L,
        Qt.Key.Key_Super_R,
    }

    _SPECIAL_KEYS = {
        Qt.Key.Key_Space: "Space",
        Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Return: "Enter",
        Qt.Key.Key_Enter: "Enter",
        Qt.Key.Key_Backspace: "Backspace",
        Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_Escape: "Esc",
        Qt.Key.Key_Up: "Up",
        Qt.Key.Key_Down: "Down",
        Qt.Key.Key_Left: "Left",
        Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Home: "Home",
        Qt.Key.Key_End: "End",
        Qt.Key.Key_PageUp: "PageUp",
        Qt.Key.Key_PageDown: "PageDown",
        Qt.Key.Key_Insert: "Insert",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        super().mousePressEvent(event)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        self.selectAll()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        self._capture_event(event)

    def event(self, event: QEvent) -> bool:  # noqa: A003
        if event.type() == QEvent.Type.ShortcutOverride and isinstance(event, QKeyEvent):
            self._capture_event(event)
            return True
        return super().event(event)

    def _capture_event(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            event.accept()
            return

        key = event.key()
        if key in {Qt.Key.Key_Backspace, Qt.Key.Key_Delete}:
            self.clear()
            event.accept()
            return

        parts: list[str] = []
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier or key == Qt.Key.Key_Control:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier or key == Qt.Key.Key_Shift:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier or key == Qt.Key.Key_Alt:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier or key in {
            Qt.Key.Key_Meta,
            Qt.Key.Key_Super_L,
            Qt.Key.Key_Super_R,
        }:
            parts.append("Win")

        key_name = self._key_name(event)
        if key_name:
            parts.append(key_name)

        if parts:
            self.setText("+".join(parts))
        event.accept()

    def _key_name(self, event: QKeyEvent) -> str | None:
        key = event.key()
        if key in self._MODIFIER_KEYS:
            return None
        if key in self._SPECIAL_KEYS:
            return self._SPECIAL_KEYS[key]
        if key in {Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R}:
            return None
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(ord("A") + (key - Qt.Key.Key_A))
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(ord("0") + (key - Qt.Key.Key_0))
        text = event.text().strip()
        if text:
            if len(text) == 1 and text.isalpha():
                return text.upper()
            return text
        native_vk = event.nativeVirtualKey() or self._vk_from_scan_code(event.nativeScanCode())
        if native_vk:
            if 0x41 <= native_vk <= 0x5A:
                return chr(native_vk)
            if 0x30 <= native_vk <= 0x39:
                return chr(native_vk)
            if 0x70 <= native_vk <= 0x87:
                return f"F{native_vk - 0x70 + 1}"
        sequence_text = QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText)
        return sequence_text or None

    def _vk_from_scan_code(self, scan_code: int) -> int:
        if scan_code <= 0 or not sys.platform.startswith("win"):
            return 0
        try:
            import ctypes

            mapvk_vsc_to_vk = 1
            return int(ctypes.windll.user32.MapVirtualKeyW(scan_code, mapvk_vsc_to_vk))
        except Exception:
            return 0


class SettingsDialog(QDialog):
    _FIELDS = (
        _FieldDescriptor("silence_threshold_db", "Silence threshold (dB)", 0.0, 100.0, 1.0, 1),
        _FieldDescriptor("silence_timeout_seconds", "Silence timeout (seconds)", 0.1, 30.0, 0.1, 2),
    )

    def __init__(self, settings: UserSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._widgets: dict[str, QDoubleSpinBox] = {}
        self._hotkey_input = HotkeyCaptureLineEdit(self)

        root = QVBoxLayout(self)
        form = QFormLayout()
        for field in self._FIELDS:
            widget = QDoubleSpinBox(self)
            widget.setMinimum(field.minimum)
            widget.setMaximum(field.maximum)
            widget.setSingleStep(field.step)
            widget.setDecimals(field.decimals)
            widget.setValue(float(getattr(settings, field.key)))
            self._widgets[field.key] = widget
            form.addRow(field.label, widget)
        self._hotkey_input.setText(settings.record_toggle_hotkey)
        self._hotkey_input.setPlaceholderText("Example: Ctrl+Shift+A")
        form.addRow("Record toggle hotkey", self._hotkey_input)
        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self) -> UserSettings:
        return UserSettings(
            silence_threshold_db=self._widgets["silence_threshold_db"].value(),
            silence_timeout_seconds=self._widgets["silence_timeout_seconds"].value(),
            record_toggle_hotkey=self._hotkey_input.text().strip(),
        )
