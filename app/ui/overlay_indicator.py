from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class OverlayIndicator(QWidget):
    _WINDOW_PADDING_X = 16
    _WINDOW_PADDING_Y = 8
    _BOTTOM_MARGIN = 24
    _STATE_LABELS = ("IDLE", "RECORDING", "PROCESSING")
    _COLORS_BY_STATE = {
        "idle": QColor("#008000"),
        "recording": QColor("#ff0000"),
        "processing": QColor("#273c75"),
    }

    def __init__(self) -> None:
        super().__init__()
        self.current_state = "idle"
        self.setWindowTitle("STT Status")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setAutoFillBackground(True)
        self.label = QLabel("READY", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self._set_fixed_size_from_longest_status()
        self.set_state("idle")
        self._reposition_bottom_center()

    def _set_fixed_size_from_longest_status(self) -> None:
        font_metrics = self.label.fontMetrics()
        label_width = max(font_metrics.horizontalAdvance(text) for text in self._STATE_LABELS)
        label_height = font_metrics.height()
        self.setFixedSize(
            label_width + self._WINDOW_PADDING_X,
            label_height + self._WINDOW_PADDING_Y,
        )

    def set_state(self, state: str) -> None:
        self.current_state = state
        self.label.setText(state.upper())
        bg_color = self._COLORS_BY_STATE.get(state, self._COLORS_BY_STATE["idle"])
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        self.setPalette(palette)
        self.label.setPalette(palette)

    def _bottom_center_position(self, screen_geometry: QRect) -> QPoint:
        x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.y() + screen_geometry.height() - self.height() - self._BOTTOM_MARGIN
        return QPoint(x, y)

    def _reposition_bottom_center(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        self.move(self._bottom_center_position(screen.availableGeometry()))

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._reposition_bottom_center()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._reposition_bottom_center()
