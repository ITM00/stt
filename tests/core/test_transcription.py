import numpy as np

from app.core.transcription import (
    EN_TEMPLATE_PATH,
    RU_TEMPLATE_PATH,
    TranscriptionResult,
    TranscriptionService,
)


def test_transcribe_returns_joined_segments() -> None:
    service = TranscriptionService(
        model_loader=lambda _: lambda _: [
            type("Segment", (), {"text": "hello"})(),
            type("Segment", (), {"text": "world"})(),
        ]
    )

    result = service.transcribe(b"fake")

    assert result == TranscriptionResult(text="hello world", template_path=EN_TEMPLATE_PATH)


def test_transcribe_selects_ru_template_for_cyrillic_text() -> None:
    service = TranscriptionService(
        model_loader=lambda _: lambda _: [type("Segment", (), {"text": "привет"})()]
    )

    result = service.transcribe(b"fake")

    assert result.template_path == RU_TEMPLATE_PATH


def test_transcribe_calls_model_transcribe_with_float32_audio() -> None:
    captured_loader_kwargs: dict[str, object] = {}

    class StubModel:
        def __init__(self) -> None:
            self.last_audio: np.ndarray | None = None

        def transcribe(self, audio, beam_size: int = 5, **kwargs):  # noqa: ANN001
            self.last_audio = audio
            assert beam_size == 5
            assert kwargs.get("language") == "en"
            assert audio.dtype == np.float32
            return [type("Segment", (), {"text": "hello"})()], {}

    stub = StubModel()

    def loader(_model_name: str, **kwargs):  # noqa: ANN001
        captured_loader_kwargs.update(kwargs)
        return stub

    service = TranscriptionService(
        model_loader=loader,
        sample_rate=16000,
        language="en",
        device="cuda",
        compute_type="float16",
    )

    pcm = np.array([1000, -1000], dtype=np.int16).tobytes()
    result = service.transcribe(pcm)

    assert stub.last_audio is not None
    assert np.allclose(stub.last_audio, np.array([1000, -1000], dtype=np.float32) / 32768.0)
    assert captured_loader_kwargs["device"] == "cuda"
    assert captured_loader_kwargs["compute_type"] == "float16"
    assert result == TranscriptionResult(text="hello", template_path=EN_TEMPLATE_PATH)


def test_transcribe_falls_back_to_local_files_only_when_online_check_fails() -> None:
    class StubModel:
        def transcribe(self, _audio, beam_size: int = 5, **kwargs):  # noqa: ANN001
            assert beam_size == 5
            assert kwargs.get("language") == "en"
            return [type("Segment", (), {"text": "offline ok"})()], {}

    calls: list[dict[str, object]] = []

    def loader(_model_name: str, **kwargs):  # noqa: ANN001
        calls.append(kwargs)
        if kwargs.get("local_files_only") is True:
            return StubModel()
        raise RuntimeError("remote metadata check failed")

    service = TranscriptionService(
        model_loader=loader,
        language="en",
        device="cuda",
        compute_type="float16",
    )

    result = service.transcribe(np.array([1, -1], dtype=np.int16).tobytes())

    assert result == TranscriptionResult(text="offline ok", template_path=EN_TEMPLATE_PATH)
    assert calls[0] == {"device": "cuda", "compute_type": "float16"}
    assert calls[1] == {
        "device": "cuda",
        "compute_type": "float16",
        "local_files_only": True,
    }
