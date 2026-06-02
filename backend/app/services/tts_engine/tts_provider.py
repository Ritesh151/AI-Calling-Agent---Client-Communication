from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, output_path: Path, voice: str | None = None, language: str | None = None) -> Path:
        ...

    @abstractmethod
    async def get_available_voices(self) -> list[str]:
        ...

    @abstractmethod
    async def validate(self) -> bool:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
