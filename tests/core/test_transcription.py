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
