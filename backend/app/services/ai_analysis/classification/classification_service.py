from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import (
    CLASSIFICATION_PROMPT,
    CLASSIFICATION_SYSTEM,
)
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class ClassificationService:
    CATEGORIES = [
        "sales_inquiry", "support", "complaint", "quotation",
        "partnership", "vendor", "recruitment", "personal", "spam", "unknown",
    ]

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def classify(self, transcript: str) -> dict[str, Any]:
        prompt = CLASSIFICATION_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=CLASSIFICATION_SYSTEM,
        )

        if not result.success:
            logger.error("Classification failed: %s", result.error)
            return self._default()

        try:
            data = json.loads(result.content)
            primary = data.get("primary_category", "unknown")
            if primary not in self.CATEGORIES:
                primary = "unknown"
            return {
                "primary_category": primary,
                "primary_confidence": float(data.get("primary_confidence", 0.0)),
                "secondary_categories": [
                    {"category": s.get("category", "unknown"), "confidence": float(s.get("confidence", 0.0))}
                    for s in data.get("secondary_categories", [])
                    if s.get("category") in self.CATEGORIES
                ],
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse classification output: %s", e)
            return self._default()

    def _default(self) -> dict[str, Any]:
        return {
            "primary_category": "unknown",
            "primary_confidence": 0.0,
            "secondary_categories": [],
        }
