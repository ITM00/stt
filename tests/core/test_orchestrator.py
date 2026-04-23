import time

from unittest.mock import Mock, call

from PySide6.QtWidgets import QApplication

from app.core.orchestrator import TranscriptionOrchestrator
from app.core.transcription import TranscriptionResult


def test_toggle_transitions_recording_processing_idle() -> None:
    qt_app = QApplication.instance() or QApplication([])

    recorder = Mock()
    recorder.stop.return_value = b"audio"
    transcriber = Mock()
    transcriber.transcribe.return_value = TranscriptionResult(
        text="hello world",
        template_path="app/templates/punctuation_signs_en.json",
    )
    postprocessor = Mock()
    postprocessor.process.return_value = "hello world"
    clipboard = Mock()
    status_sink = Mock()

    app = TranscriptionOrchestrator(
        recorder=recorder,
        transcriber=transcriber,
        postprocessor=postprocessor,
        clipboard=clipboard,
        status_sink=status_sink,
        qt_parent=qt_app,
    )

    app.toggle_recording()
    app.toggle_recording()

    deadline = time.time() + 2.0
    while time.time() < deadline and app.state != "idle":
        qt_app.processEvents()
        time.sleep(0.01)

    assert app.state == "idle"
    status_sink.update.assert_has_calls([call("recording"), call("processing"), call("idle")])
    postprocessor.process.assert_called_once_with(
        "hello world",
        template_path="app/templates/punctuation_signs_en.json",
    )
    clipboard.copy_text.assert_called_once_with("hello world")


def test_silence_timeout_triggers_processing_pipeline() -> None:
    qt_app = QApplication.instance() or QApplication([])

    recorder = Mock()
    recorder.stop.return_value = b"audio"
    transcriber = Mock()
    transcriber.transcribe.return_value = TranscriptionResult(
        text="hello world",
        template_path="app/templates/punctuation_signs_en.json",
    )
    postprocessor = Mock()
    postprocessor.process.return_value = "hello world"
    clipboard = Mock()
    status_sink = Mock()

    app = TranscriptionOrchestrator(
        recorder=recorder,
        transcriber=transcriber,
        postprocessor=postprocessor,
        clipboard=clipboard,
        status_sink=status_sink,
        qt_parent=qt_app,
    )

    app.toggle_recording()
    on_silence_timeout = recorder.start.call_args.kwargs["on_silence_timeout"]
    on_silence_timeout()

    deadline = time.time() + 2.0
    while time.time() < deadline and app.state != "idle":
        qt_app.processEvents()
        time.sleep(0.01)

    assert app.state == "idle"
    status_sink.update.assert_has_calls([call("recording"), call("processing"), call("idle")])
    postprocessor.process.assert_called_once_with(
        "hello world",
        template_path="app/templates/punctuation_signs_en.json",
    )
    clipboard.copy_text.assert_called_once_with("hello world")
