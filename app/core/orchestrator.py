from __future__ import annotations


class TranscriptionOrchestrator:
    def __init__(self, recorder, transcriber, postprocessor, clipboard, status_sink) -> None:
        self.recorder = recorder
        self.transcriber = transcriber
        self.postprocessor = postprocessor
        self.clipboard = clipboard
        self.status_sink = status_sink
        self.state = "idle"

    def toggle_recording(self) -> None:
        if self.state == "idle":
            self.recorder.start()
            self.state = "recording"
            self.status_sink.update("recording")
            return

        if self.state == "recording":
            self.state = "processing"
            self.status_sink.update("processing")
            audio_bytes = self.recorder.stop()
            transcript = self.transcriber.transcribe(audio_bytes)
            final_text = self.postprocessor.process(
                transcript.text,
                template_path=transcript.template_path,
            )
            self.clipboard.copy_text(final_text)
            self.state = "idle"
            self.status_sink.update("idle")
