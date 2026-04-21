import numpy as np

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
