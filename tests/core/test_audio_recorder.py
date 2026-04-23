import numpy as np
from unittest.mock import Mock

from app.core.audio_recorder import AudioRecorder


class _FakeStream:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.closed = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


def _fake_stream_factory(**kwargs):
    stream = _FakeStream()
    stream.kwargs = kwargs
    return stream


def test_start_sets_recording_state() -> None:
    recorder = AudioRecorder(sample_rate=16000, stream_factory=_fake_stream_factory)

    recorder.start()

    assert recorder.is_recording is True
    assert recorder._stream is not None
    assert recorder._stream.started is True


def test_stop_returns_buffered_audio_frames() -> None:
    recorder = AudioRecorder(sample_rate=16000, stream_factory=_fake_stream_factory)
    recorder.start()
    recorder.append_frame(b"ab")
    recorder.append_frame(b"cd")

    result = recorder.stop()

    assert result == b"abcd"
    assert recorder.is_recording is False
    assert recorder._stream is None


def test_stream_callback_buffers_pcm16_bytes() -> None:
    stream_holder: dict[str, _FakeStream | None] = {"stream": None}

    def factory(**kwargs):
        stream_holder["stream"] = _FakeStream()
        stream_holder["stream"].kwargs = kwargs
        return stream_holder["stream"]

    recorder = AudioRecorder(sample_rate=16000, channels=1, stream_factory=factory)
    recorder.start()

    callback = stream_holder["stream"].kwargs["callback"]
    indata = np.array([[100], [200]], dtype=np.int16)
    callback(indata, indata.shape[0], None, None)

    assert recorder.stop() == indata.astype(np.int16).tobytes()


def test_silence_timeout_invokes_callback_after_configured_duration(monkeypatch) -> None:
    stream_holder: dict[str, _FakeStream | None] = {"stream": None}
    now = [0.0]

    def fake_monotonic() -> float:
        return now[0]

    monkeypatch.setattr("app.core.audio_recorder.time.monotonic", fake_monotonic)

    def factory(**kwargs):
        stream_holder["stream"] = _FakeStream()
        stream_holder["stream"].kwargs = kwargs
        return stream_holder["stream"]

    timeout_callback = Mock()
    recorder = AudioRecorder(
        sample_rate=16000,
        channels=1,
        stream_factory=factory,
        silence_threshold_db=30.0,
        silence_timeout_seconds=3.0,
    )
    recorder.start(on_silence_timeout=timeout_callback)

    callback = stream_holder["stream"].kwargs["callback"]
    silent = np.zeros((160, 1), dtype=np.int16)
    callback(silent, silent.shape[0], None, None)  # t=0.0
    now[0] = 2.9
    callback(silent, silent.shape[0], None, None)  # t=2.9
    now[0] = 3.1
    callback(silent, silent.shape[0], None, None)  # t=3.1
    now[0] = 3.3
    callback(silent, silent.shape[0], None, None)  # one-shot

    timeout_callback.assert_called_once()
    recorder.stop()


def test_signal_above_threshold_resets_silence_timeout(monkeypatch) -> None:
    stream_holder: dict[str, _FakeStream | None] = {"stream": None}
    now = [0.0]

    def fake_monotonic() -> float:
        return now[0]

    monkeypatch.setattr("app.core.audio_recorder.time.monotonic", fake_monotonic)

    def factory(**kwargs):
        stream_holder["stream"] = _FakeStream()
        stream_holder["stream"].kwargs = kwargs
        return stream_holder["stream"]

    timeout_callback = Mock()
    recorder = AudioRecorder(
        sample_rate=16000,
        channels=1,
        stream_factory=factory,
        silence_threshold_db=30.0,
        silence_timeout_seconds=3.0,
    )
    recorder.start(on_silence_timeout=timeout_callback)

    callback = stream_holder["stream"].kwargs["callback"]
    silent = np.zeros((160, 1), dtype=np.int16)
    loud = np.full((160, 1), 100, dtype=np.int16)  # ~40 dB relative level
    callback(silent, silent.shape[0], None, None)  # t=0.0
    now[0] = 2.9
    callback(loud, loud.shape[0], None, None)  # reset timer
    now[0] = 5.5
    callback(silent, silent.shape[0], None, None)  # <3s since loud
    now[0] = 6.2
    callback(silent, silent.shape[0], None, None)  # >3s since loud

    timeout_callback.assert_called_once()
    recorder.stop()


def test_first_audio_frame_callback_fires_once() -> None:
    stream_holder: dict[str, _FakeStream | None] = {"stream": None}

    def factory(**kwargs):
        stream_holder["stream"] = _FakeStream()
        stream_holder["stream"].kwargs = kwargs
        return stream_holder["stream"]

    first_frame_callback = Mock()
    recorder = AudioRecorder(sample_rate=16000, channels=1, stream_factory=factory)
    recorder.start(on_first_audio_frame=first_frame_callback)

    callback = stream_holder["stream"].kwargs["callback"]
    frame = np.array([[100], [200]], dtype=np.int16)
    callback(frame, frame.shape[0], None, None)
    callback(frame, frame.shape[0], None, None)

    first_frame_callback.assert_called_once()
    recorder.stop()
