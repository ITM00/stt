from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from app.core.audio_recorder import AudioRecorder
from app.core.clipboard_manager import ClipboardManager
from app.core.hotkey_manager import HotkeyManager
from app.core.orchestrator import TranscriptionOrchestrator
from app.core.text_postprocessor import TextPostProcessor
from app.core.transcription import TranscriptionService
from app.ui.overlay_indicator import OverlayIndicator
from app.ui.settings_dialog import SettingsDialog
from app.ui.tray_icon import TrayIconController
from app.utils.config import load_config
from app.utils.hotkey_format import as_pynput_global_hotkey
from app.utils.logger import get_logger
from app.utils.settings_store import apply_user_settings, load_user_settings, save_user_settings

logger = get_logger(__name__)


class UiStatusSink:
    def __init__(self, overlay: OverlayIndicator, tray: TrayIconController) -> None:
        self.overlay = overlay
        self.tray = tray

    def update(self, state: str) -> None:
        self.overlay.set_state(state)
        self.tray.set_state(state)


class HotkeyBridge(QObject):
    toggle_requested = Signal()


def create_app(
    *,
    hotkey_manager: HotkeyManager | None = None,
    hotkey_listener_factory: Callable[..., Any] | None = None,
) -> tuple[QApplication, TranscriptionOrchestrator, HotkeyManager]:
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        qt_app = instance
    else:
        qt_app = QApplication([])

    config = load_config()
    overlay = OverlayIndicator()

    recorder = AudioRecorder(sample_rate=config.sample_rate)
    user_settings = load_user_settings()
    if not user_settings.record_toggle_hotkey.strip():
        user_settings.record_toggle_hotkey = config.hotkey
    apply_user_settings(recorder, user_settings)

    hotkeys = hotkey_manager or HotkeyManager(listener_factory=hotkey_listener_factory)

    bridge = HotkeyBridge()

    def run_toggle() -> None:
        logger.info("Running toggle on Qt main thread")
        try:
            orchestrator.toggle_recording()
        except Exception:
            logger.exception("toggle_recording failed")

    bridge.toggle_requested.connect(run_toggle, Qt.ConnectionType.QueuedConnection)

    def toggle_on_main_thread() -> None:
        logger.info("Global hotkey callback received")
        bridge.toggle_requested.emit()

    def register_hotkey(hotkey_value: str) -> None:
        normalized_hotkey = as_pynput_global_hotkey(hotkey_value)
        logger.info(
            "Registering global hotkey user=%s fallback=%s normalized=%s",
            hotkey_value,
            config.hotkey,
            normalized_hotkey,
        )
        hotkeys.stop()
        hotkeys.register(normalized_hotkey, toggle_on_main_thread)
        logger.info("Global hotkey listener started")

    def open_settings() -> None:
        dialog = SettingsDialog(user_settings)
        dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        anchor = tray.tray.geometry().center()
        if anchor.isNull():
            anchor = QCursor.pos()
        dialog.adjustSize()
        dialog.move(anchor.x() - dialog.width() // 2, anchor.y() - dialog.height() // 2)
        QTimer.singleShot(0, dialog.raise_)
        QTimer.singleShot(0, dialog.activateWindow)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        updated = dialog.values()
        try:
            save_user_settings(updated)
        except Exception:
            logger.exception("Failed to save user settings; keeping current runtime settings")
            return
        apply_user_settings(recorder, updated)
        user_settings.silence_threshold_db = updated.silence_threshold_db
        user_settings.silence_timeout_seconds = updated.silence_timeout_seconds
        effective_hotkey = updated.record_toggle_hotkey.strip() or config.hotkey
        try:
            register_hotkey(effective_hotkey)
        except Exception:
            logger.exception("Failed applying hotkey immediately; keeping current runtime hotkey")
            return
        user_settings.record_toggle_hotkey = effective_hotkey

    tray = TrayIconController(on_quit=qt_app.quit, on_settings=open_settings)
    status_sink = UiStatusSink(overlay=overlay, tray=tray)

    transcriber = TranscriptionService(
        model_name=config.model_name,
        sample_rate=config.sample_rate,
        language=config.language,
        device=config.whisper_device,
        compute_type=config.whisper_compute_type,
    )
    postprocessor = TextPostProcessor(template_path=config.template_path)
    clipboard = ClipboardManager()
    orchestrator = TranscriptionOrchestrator(
        recorder=recorder,
        transcriber=transcriber,
        postprocessor=postprocessor,
        clipboard=clipboard,
        status_sink=status_sink,
        qt_parent=qt_app,
    )

    effective_hotkey = user_settings.record_toggle_hotkey.strip() or config.hotkey
    register_hotkey(effective_hotkey)

    overlay.show()

    qt_app.aboutToQuit.connect(tray.tray.hide)
    qt_app.aboutToQuit.connect(hotkeys.stop)
    # Keep QObject alive for queued signal delivery.
    qt_app._hotkey_bridge = bridge  # type: ignore[attr-defined]
    qt_app._open_settings = open_settings  # type: ignore[attr-defined]
    return qt_app, orchestrator, hotkeys


def main() -> int:
    logger.info("Starting STT desktop app")
    app, _, _ = create_app()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
