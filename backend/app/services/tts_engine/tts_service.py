from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.tts_engine.edge_tts_provider import EdgeTTSProvider
from app.services.tts_engine.local_tts_provider import LocalTTSProvider
from app.services.tts_engine.openai_tts_provider import OpenAITTSProvider
from app.services.tts_engine.tts_provider import TTSProvider

logger = logging.getLogger(__name__)

class TTSFactory:
    _providers: dict[str, TTSProvider] = {}
    _cache_dir: Path = Path(settings.TTS_CACHE_DIR)

    @classmethod
    def get_provider(cls, name: str | None = None) -> TTSProvider:
        provider_name = name or settings.TTS_DEFAULT_PROVIDER
        if provider_name not in cls._providers:
            cls._providers[provider_name] = cls._create_provider(provider_name)
        return cls._providers[provider_name]

    @classmethod
    def _create_provider(cls, name: str) -> TTSProvider:
        providers = {
            "edge": EdgeTTSProvider,
            "openai": OpenAITTSProvider,
            "local": LocalTTSProvider,
        }
        provider_cls = providers.get(name)
        if not provider_cls:
            logger.warning("Unknown TTS provider %s, falling back to edge", name)
            provider_cls = EdgeTTSProvider
        return provider_cls()

    @classmethod
    async def generate_speech(cls, text: str, voice: str | None = None, language: str | None = None, provider_name: str | None = None) -> Path:
        cls._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.md5(f"{text}:{voice}:{language}".encode()).hexdigest()
        cache_path = cls._cache_dir / f"{cache_key}.wav"

        if settings.TTS_CACHE_ENABLED and cache_path.exists():
            logger.debug("TTS cache hit for key %s", cache_key)
            return cache_path

        provider = cls.get_provider(provider_name)
        providers_to_try = [provider]

        if provider_name is None:
            for pname in ["edge", "openai", "local"]:
                if pname != (provider_name or settings.TTS_DEFAULT_PROVIDER):
                    providers_to_try.append(cls.get_provider(pname))

        last_error: Exception | None = None
        for prov in providers_to_try:
            try:
                result = await prov.generate_speech(text, cache_path, voice, language)
                logger.info("TTS generated via %s provider", prov.name)
                return result
            except Exception as e:
                last_error = e
                logger.warning("TTS provider %s failed: %s", prov.name, e)
                continue

        raise RuntimeError(f"All TTS providers failed. Last error: {last_error}")
