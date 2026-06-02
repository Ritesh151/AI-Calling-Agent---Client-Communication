from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import (
    SUMMARIZATION_PROMPT,
    SUMMARIZATION_SYSTEM,
)
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class SummarizationService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def generate_summary(self, transcript: str) -> dict[str, Any]:
        prompt = SUMMARIZATION_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=SUMMARIZATION_SYSTEM,
        )

        if not result.success:
            logger.error("Summarization failed: %s", result.error)
            return self._default_summary()

        try:
            data = json.loads(result.content)
            return {
                "summary": data.get("summary", ""),
                "short_summary": data.get("short_summary", "")[:500],
                "action_items": data.get("action_items", []),
                "callback_required": data.get("callback_required", "unknown"),
                "callback_reason": data.get("callback_reason", ""),
                "urgency_level": data.get("urgency", "unknown"),
                "urgency_reason": data.get("urgency_reason", ""),
                "sentiment": data.get("sentiment", "unknown"),
                "sentiment_reasoning": data.get("sentiment_reasoning", ""),
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse summary output: %s", e)
            return self._default_summary()

    def _default_summary(self) -> dict[str, Any]:
        return {
            "summary": "",
            "short_summary": "",
            "action_items": [],
            "callback_required": "unknown",
            "callback_reason": "",
            "urgency_level": "unknown",
            "urgency_reason": "",
            "sentiment": "unknown",
            "sentiment_reasoning": "",
        }
