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


def test_tray_settings_action_triggers_callback() -> None:
    _ensure_app()
    calls = {"count": 0}

    def on_settings() -> None:
        calls["count"] += 1

    tray = TrayIconController(on_settings=on_settings)
    action = next(a for a in tray.menu.actions() if a.text() == "Settings")
    action.trigger()
    assert calls["count"] == 1
