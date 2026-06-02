from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import URGENCY_PROMPT, URGENCY_SYSTEM
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class UrgencyService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def detect_urgency(self, transcript: str) -> dict[str, Any]:
        prompt = URGENCY_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=URGENCY_SYSTEM,
        )

        if not result.success:
            logger.error("Urgency detection failed: %s", result.error)
            return self._default()

        try:
            data = json.loads(result.content)
            urgency = data.get("urgency", "unknown")
            if urgency not in ("low", "medium", "high", "critical"):
                urgency = "unknown"
            return {
                "urgency": urgency,
                "confidence": float(data.get("confidence", 0.0)),
                "reasoning": data.get("reasoning", ""),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse urgency output: %s", e)
            return self._default()

    def _default(self) -> dict[str, Any]:
        return {"urgency": "unknown", "confidence": 0.0, "reasoning": ""}
