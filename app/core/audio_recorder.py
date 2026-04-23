from __future__ import annotations

import math
import time
from collections.abc import Callable
from threading import Thread
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
        silence_threshold_db: float = 30.0,
        silence_timeout_seconds: float = 3.0,
    ) -> None:
        self._logger = get_logger(__name__)
        self.sample_rate = sample_rate
        self._stream_factory = stream_factory
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.silence_threshold_db = silence_threshold_db
        self.silence_timeout_seconds = silence_timeout_seconds
        self.is_recording = False
        self._frames: list[bytes] = []
        self._stream: Any | None = None
        self._silence_timeout_callback: Callable[[], None] | None = None
        self._first_audio_frame_callback: Callable[[], None] | None = None
        self._first_audio_frame_seen = False
        self._last_signal_time: float | None = None
        self._silence_timeout_fired = False

    def start(
        self,
        on_silence_timeout: Callable[[], None] | None = None,
        on_first_audio_frame: Callable[[], None] | None = None,
    ) -> None:
        self._logger.info(
            "AudioRecorder.start called sample_rate=%s channels=%s",
            self.sample_rate,
            self.channels,
        )
        self._frames.clear()
        self.is_recording = True
        self._silence_timeout_callback = on_silence_timeout
        self._first_audio_frame_callback = on_first_audio_frame
        self._first_audio_frame_seen = False
        self._last_signal_time = time.monotonic()
        self._silence_timeout_fired = False
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

        assert self._stream is not None
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
        self._silence_timeout_callback = None
        self._first_audio_frame_callback = None
        self._first_audio_frame_seen = False
        self._last_signal_time = None
        self._silence_timeout_fired = False
        output = b"".join(self._frames)
        self._logger.info("AudioRecorder.stop buffered_bytes=%s", len(output))
        return output

    def _pcm16_from_input(self, indata: np.ndarray) -> np.ndarray:
        if np.issubdtype(indata.dtype, np.floating):
            clipped = np.clip(indata, -1.0, 1.0)
            return np.ascontiguousarray(clipped * 32767.0).astype(np.int16, copy=False)
        return np.ascontiguousarray(indata).astype(np.int16, copy=False)

    def _signal_db(self, pcm: np.ndarray) -> float:
        # 0..100 scale where 100 is full-scale digital amplitude.
        samples = pcm.astype(np.float32, copy=False)
        rms = float(np.sqrt(np.mean(np.square(samples))))
        if rms <= 0.0:
            return float("-inf")
        dbfs = 20.0 * math.log10(rms / 32768.0)
        return dbfs + 100.0

    def _sounddevice_callback(self, indata, frames, time_info, status) -> None:  # noqa: ARG002
        if not self.is_recording:
            return

        if status:
            self._logger.warning("sounddevice callback status=%s", status)
        if not self._first_audio_frame_seen:
            self._first_audio_frame_seen = True
            if self._first_audio_frame_callback is not None:
                Thread(target=self._first_audio_frame_callback, daemon=True).start()
        pcm = self._pcm16_from_input(indata)
        db_level = self._signal_db(pcm)
        now = time.monotonic()
        if db_level >= self.silence_threshold_db:
            self._last_signal_time = now
            self._silence_timeout_fired = False
        elif (
            self._last_signal_time is not None
            and not self._silence_timeout_fired
            and (now - self._last_signal_time) >= self.silence_timeout_seconds
        ):
            self._silence_timeout_fired = True
            self._logger.info(
                "Silence timeout reached: level_db=%.2f threshold_db=%.2f timeout_s=%.2f",
                db_level,
                self.silence_threshold_db,
                self.silence_timeout_seconds,
            )
            if self._silence_timeout_callback is not None:
                Thread(target=self._silence_timeout_callback, daemon=True).start()
        self.append_frame(pcm.tobytes())
