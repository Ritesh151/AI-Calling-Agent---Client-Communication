from __future__ import annotations

import logging

from app.core.config import settings
from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.local_ai_provider import LocalAIProvider
from app.services.ai_analysis.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    _instances: dict[str, AIProvider] = {}

    @classmethod
    def get_provider(cls, name: str | None = None) -> AIProvider:
        provider_name = name or settings.AI_ANALYSIS_PROVIDER
        if provider_name not in cls._instances:
            cls._instances[provider_name] = cls._create(provider_name)
        return cls._instances[provider_name]

    @classmethod
    def _create(cls, name: str) -> AIProvider:
        if name == "openai":
            return OpenAIProvider()
        elif name == "local":
            return LocalAIProvider()
        logger.warning("Unknown AI provider %s, falling back to openai", name)
        return OpenAIProvider()

    @classmethod
    def reset(cls) -> None:
        cls._instances.clear()
