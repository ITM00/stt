from __future__ import annotations

from PySide6.QtWidgets import QApplication


def create_app() -> tuple[QApplication, object]:
    qt_app = QApplication.instance() or QApplication([])
    orchestrator = object()
    return qt_app, orchestrator
