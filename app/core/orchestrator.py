from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

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
        status_sink,
        *,
        qt_parent: QObject | None = None,
    ) -> None:
        self._logger = get_logger(__name__)
        self.recorder = recorder
        self.transcriber = transcriber
        self.postprocessor = postprocessor
        self.clipboard = clipboard
        self.status_sink = status_sink
        self.state = "idle"
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="stt-worker")
        self._bridge: _ProcessingBridge | None = None
        if qt_parent is not None:
            self._bridge = _ProcessingBridge(qt_parent)
            self._bridge.finished.connect(self._finish_success, Qt.ConnectionType.QueuedConnection)
            self._bridge.failed.connect(self._finish_failure, Qt.ConnectionType.QueuedConnection)

    def toggle_recording(self) -> None:
        self._logger.info("toggle_recording called state=%s", self.state)
        if self.state == "idle":
            self.recorder.start()
            self.state = "recording"
            self.status_sink.update("recording")
            self._logger.info("state transitioned to recording")
            return

        if self.state == "recording":
            self.state = "processing"
            self.status_sink.update("processing")
            self._logger.info("state transitioned to processing")
            self._executor.submit(self._process_audio_job)
            return

    def _process_audio_job(self) -> None:
        try:
            audio_bytes = self.recorder.stop()
            transcript = self.transcriber.transcribe(audio_bytes)
            print(f"[faster-whisper raw] {transcript.text}", flush=True)
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
