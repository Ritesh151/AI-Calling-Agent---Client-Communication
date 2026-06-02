from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.transcript_schema import TranscriptCreate
from app.services.transcription.transcription_provider import TranscriptionProvider

logger = logging.getLogger(__name__)


class FasterWhisperProvider(TranscriptionProvider):
    def __init__(self) -> None:
        self._model: Any = None
        self._model_size = settings.TRANSCRIPTION_MODEL_SIZE
        self._device = settings.TRANSCRIPTION_DEVICE
        self._compute_type = settings.TRANSCRIPTION_COMPUTE_TYPE

    def transcribe(self, audio_path: Path, language: str | None = None) -> TranscriptCreate:
        model = self._get_model()
        lang = language or settings.TRANSCRIPTION_LANGUAGE
        start_time = time.monotonic()

        segments, info = model.transcribe(
            str(audio_path),
            language=lang,
            beam_size=settings.TRANSCRIPTION_BEAM_SIZE,
        )
        segments_list = list(segments)

        full_text = " ".join(s.text for s in segments_list).strip()
        processing_time = time.monotonic() - start_time
        word_count = len(full_text.split()) if full_text else 0
        avg_confidence = (
            sum(s.avg_logprob for s in segments_list) / len(segments_list)
            if segments_list else 0.0
        )
        detected_language = info.language if info else lang

        return TranscriptCreate(
            language=detected_language,
            transcript_text=full_text,
            raw_transcript=full_text,
            confidence_score=float(avg_confidence),
            processing_time=processing_time,
        )

    def validate(self) -> bool:
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def _get_model(self):
        if self._model is None:
            try:
                import faster_whisper
                logger.info(
                    "Loading faster-whisper model %s on %s (%s)",
                    self._model_size,
                    self._device,
                    self._compute_type,
                )
                self._model = faster_whisper.WhisperModel(
                    model_size_or_path=self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
            except ImportError:
                raise RuntimeError("faster-whisper package not installed")
        return self._model
