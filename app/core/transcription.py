from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from app.utils.logger import get_logger

EN_TEMPLATE_PATH = "app/templates/punctuation_signs_en.json"
RU_TEMPLATE_PATH = "app/templates/punctuation_signs_ru.json"

CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    template_path: str


class TranscriptionService:
    def __init__(
        self,
        model_name: str = "small",
        model_loader: Any | None = None,
        *,
        sample_rate: int = 16000,
        language: str | None = "en",
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> None:
        self._logger = get_logger(__name__)
        self._model_loader = model_loader
        self._model_name = model_name
        self._model: Any | None = None
        self.sample_rate = sample_rate
        self.language = language
        self.device = device
        self.compute_type = compute_type

    def _get_model(self) -> Any:
        if self._model_loader is None:
            from faster_whisper import WhisperModel

            self._model_loader = WhisperModel
        if self._model is None:
            self._logger.info(
                "Loading Whisper model name=%s device=%s compute_type=%s",
                self._model_name,
                self.device,
                self.compute_type,
            )
            try:
                self._model = self._model_loader(
                    self._model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except TypeError:
                self._logger.info("Model loader does not accept device/compute_type kwargs")
                self._model = self._model_loader(self._model_name)
        return self._model

    def _pcm16_bytes_to_float32(self, audio_bytes: bytes) -> np.ndarray:
        if not audio_bytes:
            return np.zeros((0,), dtype=np.float32)
        pcm = np.frombuffer(audio_bytes, dtype=np.int16)
        return (pcm.astype(np.float32) / 32768.0).reshape(-1)

    def transcribe(self, audio_bytes: bytes) -> TranscriptionResult:
        audio = self._pcm16_bytes_to_float32(audio_bytes)
        model = self._get_model()

        if hasattr(model, "transcribe"):
            kwargs: dict[str, Any] = {}
            if self.language:
                kwargs["language"] = self.language
            segments, _info = model.transcribe(audio, beam_size=5, **kwargs)
        else:
            segments = model(audio_bytes)

        text = " ".join(segment.text.strip() for segment in segments).strip()
        template_path = RU_TEMPLATE_PATH if CYRILLIC_PATTERN.search(text) else EN_TEMPLATE_PATH
        return TranscriptionResult(text=text, template_path=template_path)
