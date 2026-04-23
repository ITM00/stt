from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication

from app.ui.overlay_indicator import OverlayIndicator


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_overlay_updates_visual_state() -> None:
    _ensure_app()
    overlay = OverlayIndicator()
    overlay.set_state("idle")
    initial_size = overlay.size()

    assert overlay.palette().color(overlay.backgroundRole()).name().lower() == "#008000"
    assert overlay.label.alignment() & Qt.AlignmentFlag.AlignCenter

    overlay.set_state("recording")

    assert overlay.current_state == "recording"
    assert overlay.label.text() == "RECORDING"
    assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert overlay.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert overlay.palette().color(overlay.backgroundRole()).name().lower() == "#ff0000"

    overlay.set_state("warmup")
    assert overlay.current_state == "warmup"
    assert overlay.label.text() == "WARMUP"

    overlay.set_state("processing")
    assert overlay.label.text() == "PROCESSING"
    assert overlay.size() == initial_size


def test_overlay_bottom_center_position_calculation() -> None:
    _ensure_app()
    overlay = OverlayIndicator()
    screen_geometry = QRect(0, 0, 1920, 1080)

    position = overlay._bottom_center_position(screen_geometry)

    assert position.x() == (1920 - overlay.width()) // 2
    assert position.y() == 1080 - overlay.height() - overlay._BOTTOM_MARGIN
