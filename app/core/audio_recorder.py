from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
from app.utils.logger import get_logger


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int,
        stream_factory: Callable[..., Any] | None = None,
        channels: int = 1,
        dtype: str = "int16",
        blocksize: int = 1024,
    ) -> None:
        self._logger = get_logger(__name__)
        self.sample_rate = sample_rate
        self._stream_factory = stream_factory
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.is_recording = False
        self._frames: list[bytes] = []
        self._stream: Any | None = None

    def start(self) -> None:
        self._logger.info("AudioRecorder.start called sample_rate=%s channels=%s", self.sample_rate, self.channels)
        self._frames.clear()
        self.is_recording = True
        if self._stream_factory is None:
            import sounddevice as sd

            self._logger.info("Creating sounddevice input stream")
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.blocksize,
                callback=self._sounddevice_callback,
            )
        else:
            try:
                self._logger.info("Creating injected audio stream via kwargs factory")
                self._stream = self._stream_factory(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.blocksize,
                    callback=self._sounddevice_callback,
                )
            except TypeError:
                self._logger.info("Falling back to positional stream_factory signature")
                self._stream = self._stream_factory(self._sounddevice_callback, self.sample_rate)

        self._stream.start()
        self._logger.info("Audio stream started")

    def append_frame(self, frame: bytes) -> None:
        if self.is_recording:
            self._frames.append(frame)

    def stop(self) -> bytes:
        self._logger.info("AudioRecorder.stop called")
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.is_recording = False
        output = b"".join(self._frames)
        self._logger.info("AudioRecorder.stop buffered_bytes=%s", len(output))
        return output

    def _sounddevice_callback(self, indata, frames, time_info, status) -> None:  # noqa: ARG002
        if not self.is_recording:
            return

        if status:
            self._logger.warning("sounddevice callback status=%s", status)
        pcm = np.ascontiguousarray(indata).astype(np.int16, copy=False)
        self.append_frame(pcm.tobytes())
