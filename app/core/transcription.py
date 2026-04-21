from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

EN_TEMPLATE_PATH = "app/templates/punctuation_signs_en.json"
RU_TEMPLATE_PATH = "app/templates/punctuation_signs_ru.json"

CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    template_path: str


class TranscriptionService:
    def __init__(self, model_name: str = "small", model_loader: Any | None = None) -> None:
        if model_loader is None:
            from faster_whisper import WhisperModel

            model_loader = WhisperModel

        self._model_loader = model_loader
        self._model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            self._model = self._model_loader(self._model_name)
        return self._model

    def transcribe(self, audio_bytes: bytes) -> TranscriptionResult:
        segments = self._get_model()(audio_bytes)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        template_path = RU_TEMPLATE_PATH if CYRILLIC_PATTERN.search(text) else EN_TEMPLATE_PATH
        return TranscriptionResult(text=text, template_path=template_path)
