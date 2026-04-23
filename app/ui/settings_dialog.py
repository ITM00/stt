from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, QEasingCurve, QEvent, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QIcon, QKeyEvent, QKeySequence, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QCheckBox,
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

    _SPECIAL_KEYS: dict[int, str] = {
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


class SwitchCheckBox(QCheckBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText("")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(38, 20)

        self._thumb_margin = 2.0
        self._thumb_diameter = 16.0
        self._thumb_pos = self._thumb_margin
        self._bg_off = QColor("#9AA0A6")
        self._bg_on = QColor("#2D9CDB")
        self._thumb_color = QColor("#FFFFFF")

        self._animation = QPropertyAnimation(self, b"thumb_pos", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.stateChanged.connect(self._start_transition)

    def _get_thumb_pos(self) -> float:
        return self._thumb_pos

    def _set_thumb_pos(self, value: float) -> None:
        self._thumb_pos = value
        self.update()

    thumb_pos = Property(float, _get_thumb_pos, _set_thumb_pos)

    def _thumb_range(self) -> tuple[float, float]:
        min_pos = self._thumb_margin
        max_pos = self.width() - self._thumb_diameter - self._thumb_margin
        return min_pos, max_pos

    def _start_transition(self, _state: int) -> None:
        min_pos, max_pos = self._thumb_range()
        self._animation.stop()
        self._animation.setStartValue(self._thumb_pos)
        self._animation.setEndValue(max_pos if self.isChecked() else min_pos)
        self._animation.start()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        min_pos, max_pos = self._thumb_range()
        self._thumb_pos = max_pos if self.isChecked() else min_pos

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        radius = self.height() / 2
        background = self._bg_on if self.isChecked() else self._bg_off
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(self.rect(), radius, radius)

        painter.setBrush(self._thumb_color)
        painter.drawEllipse(
            int(self._thumb_pos),
            int(self._thumb_margin),
            int(self._thumb_diameter),
            int(self._thumb_diameter),
        )


class SettingsDialog(QDialog):
    _FIELDS = (
        _FieldDescriptor("silence_threshold_db", "Silence threshold (dB)", 0.0, 100.0, 1.0, 1),
        _FieldDescriptor("silence_timeout_seconds", "Silence timeout (seconds)", 0.1, 30.0, 0.1, 2),
    )

    def __init__(self, settings: UserSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        icon_path = Path(__file__).with_name("icons") / "stt_icon_24.png"
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            self.setWindowIcon(icon)
        self._widgets: dict[str, QDoubleSpinBox] = {}
        self._hotkey_input = HotkeyCaptureLineEdit(self)
        self._auto_paste_checkbox = SwitchCheckBox(self)

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
        self._auto_paste_checkbox.setChecked(settings.auto_paste_enabled)
        form.addRow("Auto-paste after transcription", self._auto_paste_checkbox)
        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self) -> UserSettings:
        return UserSettings(
            silence_threshold_db=self._widgets["silence_threshold_db"].value(),
            silence_timeout_seconds=self._widgets["silence_timeout_seconds"].value(),
            record_toggle_hotkey=self._hotkey_input.text().strip(),
            auto_paste_enabled=self._auto_paste_checkbox.isChecked(),
        )
