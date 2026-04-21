from __future__ import annotations

from collections.abc import Callable
from typing import Any


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int,
        stream_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self._stream_factory = stream_factory
        self.is_recording = False
        self._frames: list[bytes] = []

    def start(self) -> None:
        self._frames.clear()
        self.is_recording = True

    def append_frame(self, frame: bytes) -> None:
        if self.is_recording:
            self._frames.append(frame)

    def stop(self) -> bytes:
        self.is_recording = False
        return b"".join(self._frames)
