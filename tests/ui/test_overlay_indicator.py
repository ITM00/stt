from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.overlay_indicator import OverlayIndicator


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_overlay_updates_visual_state() -> None:
    _ensure_app()
    overlay = OverlayIndicator()

    overlay.set_state("recording")

    assert overlay.current_state == "recording"
    assert overlay.label.text() == "RECORDING"
    assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
