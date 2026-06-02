from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.services.tts_engine.tts_provider import TTSProvider

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    def __init__(self) -> None:
        self._available = False

    @property
    def name(self) -> str:
        return "edge"

    async def generate_speech(self, text: str, output_path: Path, voice: str | None = None, language: str | None = None) -> Path:
        try:
            import edge_tts
            voice = voice or "en-US-JennyNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            logger.info("Edge TTS generated speech to %s", output_path)
            return output_path
        except ImportError:
            raise RuntimeError("edge-tts package not installed")
        except Exception as e:
            logger.error("Edge TTS failed: %s", e)
            raise

    async def get_available_voices(self) -> list[str]:
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return [v["ShortName"] for v in voices]
        except Exception:
            return ["en-US-JennyNeural"]

    async def validate(self) -> bool:
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            self._available = len(voices) > 0
            return self._available
        except Exception:
            self._available = False
            return False
