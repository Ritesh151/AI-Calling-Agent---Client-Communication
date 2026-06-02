from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import ENTITY_PROMPT, ENTITY_SYSTEM
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class EntityExtractionService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def extract_entities(self, transcript: str) -> list[dict[str, Any]]:
        prompt = ENTITY_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=ENTITY_SYSTEM,
        )

        if not result.success:
            logger.error("Entity extraction failed: %s", result.error)
            return []

        try:
            data = json.loads(result.content)
            entities = data.get("entities", [])
            validated = []
            for entity in entities:
                validated.append({
                    "entity_type": entity.get("entity_type", "unknown"),
                    "entity_value": str(entity.get("entity_value", "")),
                    "confidence_score": float(entity.get("confidence", 0.5)),
                })
            return validated
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse entity output: %s", e)
            return []
