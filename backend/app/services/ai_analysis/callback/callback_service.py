from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import CALLBACK_PROMPT, CALLBACK_SYSTEM
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class CallbackService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def detect_callback(self, transcript: str) -> dict[str, Any]:
        prompt = CALLBACK_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=CALLBACK_SYSTEM,
        )

        if not result.success:
            logger.error("Callback detection failed: %s", result.error)
            return self._default()

        try:
            data = json.loads(result.content)
            callback = data.get("callback_required", "no")
            if callback not in ("yes", "recommended", "no"):
                callback = "unknown"
            return {
                "callback_required": callback,
                "confidence": float(data.get("confidence", 0.0)),
                "reasoning": data.get("reasoning", ""),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse callback output: %s", e)
            return self._default()

    def _default(self) -> dict[str, Any]:
        return {"callback_required": "unknown", "confidence": 0.0, "reasoning": ""}
