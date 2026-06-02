from __future__ import annotations

import logging
from pathlib import Path

from app.services.tts_engine.tts_provider import TTSProvider

logger = logging.getLogger(__name__)


class LocalTTSProvider(TTSProvider):
    def __init__(self) -> None:
        self._available = False

    @property
    def name(self) -> str:
        return "local"

    async def generate_speech(self, text: str, output_path: Path, voice: str | None = None, language: str | None = None) -> Path:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            if voice:
                voices = engine.getProperty("voices")
                for v in voices:
                    if voice.lower() in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
            if language:
                engine.setProperty("language", language)
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            logger.info("Local TTS generated speech to %s", output_path)
            return output_path
        except ImportError:
            raise RuntimeError("pyttsx3 package not installed")
        except Exception as e:
            logger.error("Local TTS failed: %s", e)
            raise

    async def get_available_voices(self) -> list[str]:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return [v.name for v in engine.getProperty("voices")]
        except Exception:
            return ["default"]

    async def validate(self) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            self._available = True
            return True
        except Exception:
            self._available = False
            return False
