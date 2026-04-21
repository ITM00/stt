from PySide6.QtWidgets import QApplication

from app.ui.tray_icon import TrayIconController


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_tray_tooltip_reflects_state() -> None:
    _ensure_app()
    tray = TrayIconController()

    tray.set_state("processing")

    assert tray.current_state == "processing"
    assert "PROCESSING" in tray.tray.toolTip()
