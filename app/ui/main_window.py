from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from app.utils.config import AppConfig


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.setWindowTitle("STT Desktop")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        hotkey_label = QLabel(f"Hotkey: {config.hotkey}")
        model_label = QLabel(f"Model: {config.model_name}")
        template_label = QLabel(f"Template: {config.template_path}")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.addWidget(hotkey_label)
        layout.addWidget(model_label)
        layout.addWidget(template_label)
        container.setLayout(layout)
        self.setCentralWidget(container)
