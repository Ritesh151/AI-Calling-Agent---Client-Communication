from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.services.tts_engine.tts_provider import TTSProvider

logger = logging.getLogger(__name__)


class OpenAITTSProvider(TTSProvider):
    def __init__(self) -> None:
        self._available = False

    @property
    def name(self) -> str:
        return "openai"

    async def generate_speech(self, text: str, output_path: Path, voice: str | None = None, language: str | None = None) -> Path:
        if not settings.TTS_OPENAI_API_KEY:
            raise RuntimeError("OpenAI API key not configured")
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.TTS_OPENAI_API_KEY)
            voice = voice or settings.TTS_OPENAI_VOICE
            response = await client.audio.speech.create(
                model=settings.TTS_OPENAI_MODEL,
                voice=voice,
                input=text,
            )
            await response.stream_to_file(str(output_path))
            logger.info("OpenAI TTS generated speech to %s", output_path)
            return output_path
        except ImportError:
            raise RuntimeError("openai package not installed")
        except Exception as e:
            logger.error("OpenAI TTS failed: %s", e)
            raise

    async def get_available_voices(self) -> list[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    async def validate(self) -> bool:
        if not settings.TTS_OPENAI_API_KEY:
            self._available = False
            return False
        try:
            import openai
            self._available = True
            return True
        except ImportError:
            self._available = False
            return False
