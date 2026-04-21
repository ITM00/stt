from unittest.mock import Mock, call

from app.core.orchestrator import TranscriptionOrchestrator
from app.core.transcription import TranscriptionResult


def test_toggle_transitions_recording_processing_idle() -> None:
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
    )

    app.toggle_recording()
    app.toggle_recording()

    assert app.state == "idle"
    status_sink.update.assert_has_calls([call("recording"), call("processing"), call("idle")])
    postprocessor.process.assert_called_once_with(
        "hello world",
        template_path="app/templates/punctuation_signs_en.json",
    )
    clipboard.copy_text.assert_called_once_with("hello world")
