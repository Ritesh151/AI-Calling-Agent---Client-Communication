from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.transcript_schema import TranscriptCreate


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path, language: str | None = None) -> TranscriptCreate:
        ...

    @abstractmethod
    def validate(self) -> bool:
        ...
