from app.core.audio_recorder import AudioRecorder


def test_start_sets_recording_state() -> None:
    recorder = AudioRecorder(sample_rate=16000)

    recorder.start()

    assert recorder.is_recording is True


def test_stop_returns_buffered_audio_frames() -> None:
    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()
    recorder.append_frame(b"ab")
    recorder.append_frame(b"cd")

    result = recorder.stop()

    assert result == b"abcd"
    assert recorder.is_recording is False
