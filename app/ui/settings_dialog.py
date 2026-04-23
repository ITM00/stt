from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
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


class SettingsDialog(QDialog):
    _FIELDS = (
        _FieldDescriptor("silence_threshold_db", "Silence threshold (dB)", 0.0, 100.0, 1.0, 1),
        _FieldDescriptor("silence_timeout_seconds", "Silence timeout (seconds)", 0.1, 30.0, 0.1, 2),
    )

    def __init__(self, settings: UserSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._widgets: dict[str, QDoubleSpinBox] = {}

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
        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self) -> UserSettings:
        return UserSettings(
            silence_threshold_db=self._widgets["silence_threshold_db"].value(),
            silence_timeout_seconds=self._widgets["silence_timeout_seconds"].value(),
        )
