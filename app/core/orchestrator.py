from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from PySide6.QtCore import QObject, Qt, Signal

from app.utils.logger import get_logger


class _ProcessingBridge(QObject):
    finished = Signal(str, str)
    failed = Signal()


class TranscriptionOrchestrator:
    def __init__(
        self,
        recorder,
        transcriber,
        postprocessor,
        clipboard,
        paste_manager,
        status_sink,
        *,
        auto_paste_enabled: bool = False,
        qt_parent: QObject | None = None,
    ) -> None:
        self._logger = get_logger(__name__)
        self.recorder = recorder
        self.transcriber = transcriber
        self.postprocessor = postprocessor
        self.clipboard = clipboard
        self.paste_manager = paste_manager
        self.status_sink = status_sink
        self.auto_paste_enabled = auto_paste_enabled
        self.state = "idle"
        self._state_lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="stt-worker")
        self._bridge: _ProcessingBridge | None = None
        if qt_parent is not None:
            self._bridge = _ProcessingBridge(qt_parent)
            self._bridge.finished.connect(self._finish_success, Qt.ConnectionType.QueuedConnection)
            self._bridge.failed.connect(self._finish_failure, Qt.ConnectionType.QueuedConnection)

    def toggle_recording(self) -> None:
        self._logger.info("toggle_recording called state=%s", self.state)
        with self._state_lock:
            if self.state == "idle":
                if self.auto_paste_enabled:
                    self.paste_manager.capture_recording_target()
                self.recorder.start(on_silence_timeout=self._on_silence_timeout)
                self.state = "recording"
                self.status_sink.update("recording")
                self._logger.info("state transitioned to recording")
                return

            if self.state == "recording":
                self._start_processing_locked(trigger="manual")
                return

    def _start_processing_locked(self, *, trigger: str) -> None:
        self.state = "processing"
        self.status_sink.update("processing")
        self._logger.info("state transitioned to processing trigger=%s", trigger)
        self._executor.submit(self._process_audio_job)

    def _on_silence_timeout(self) -> None:
        with self._state_lock:
            if self.state != "recording":
                return
            self._start_processing_locked(trigger="silence-timeout")

    def _process_audio_job(self) -> None:
        try:
            audio_bytes = self.recorder.stop()
            transcript = self.transcriber.transcribe(audio_bytes)
            # print(f"[faster-whisper raw] {transcript.text}", flush=True)
            final_text = self.postprocessor.process(
                transcript.text,
                template_path=transcript.template_path,
            )
            if self._bridge is not None:
                self._bridge.finished.emit(final_text, transcript.template_path)
            else:
                self._finish_success(final_text, transcript.template_path)
        except Exception:
            self._logger.exception("processing pipeline failed")
            if self._bridge is not None:
                self._bridge.failed.emit()
            else:
                self._finish_failure()

    def _finish_success(self, final_text: str, template_path: str) -> None:
        self.clipboard.copy_text(final_text)
        if self.auto_paste_enabled:
            self.paste_manager.paste_to_target_or_active()
        self.state = "idle"
        self.status_sink.update("idle")
        self._logger.info(
            "state transitioned to idle; copied_chars=%s template=%s",
            len(final_text),
            template_path,
        )

    def _finish_failure(self) -> None:
        self.state = "idle"
        self.status_sink.update("idle")
