from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class OverlayIndicator(QWidget):
    _STYLE_BY_STATE = {
        "idle": "background-color: #2f3542; color: #f1f2f6;",
        "recording": "background-color: #c23616; color: #ffffff;",
        "processing": "background-color: #273c75; color: #ffffff;",
    }

    def __init__(self) -> None:
        super().__init__()
        self.current_state = "idle"
        self.setWindowTitle("STT Status")
        self.label = QLabel("READY", self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        self.current_state = state
        self.label.setText(state.upper())
        self.setStyleSheet(self._STYLE_BY_STATE.get(state, self._STYLE_BY_STATE["idle"]))
