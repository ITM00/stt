from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayIconController:
    def __init__(
        self,
        on_quit: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication must be created before TrayIconController")

        self.current_state = "idle"
        self.tray = QSystemTrayIcon(self._resolve_icon(app), app)
        self.tray.setToolTip("STT Desktop - IDLE")

        self.menu = QMenu()
        settings_action = QAction("Settings", self.menu)
        settings_action.triggered.connect(on_settings or (lambda: None))
        self.menu.addAction(settings_action)

        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(on_quit or app.quit)
        self.menu.addAction(quit_action)
        self.tray.setContextMenu(self.menu)
        self.tray.setVisible(True)

    def _resolve_icon(self, app: QApplication) -> QIcon:
        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        if icon.isNull():
            return QIcon()
        return icon

    def set_state(self, state: str) -> None:
        self.current_state = state
        self.tray.setToolTip(f"STT Desktop - {state.upper()}")
