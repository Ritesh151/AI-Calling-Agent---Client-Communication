from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai_analysis.ai_provider import AIProvider
from app.services.ai_analysis.prompt_templates import SENTIMENT_PROMPT, SENTIMENT_SYSTEM
from app.services.ai_analysis.provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProviderFactory.get_provider()

    def analyze_sentiment(self, transcript: str) -> dict[str, Any]:
        prompt = SENTIMENT_PROMPT.format(transcript=transcript[:8000])
        result = self._provider.structured_analysis(
            prompt=prompt,
            output_format={},
            system_prompt=SENTIMENT_SYSTEM,
        )

        if not result.success:
            logger.error("Sentiment analysis failed: %s", result.error)
            return self._default()

        try:
            data = json.loads(result.content)
            sentiment = data.get("sentiment", "unknown")
            if sentiment not in ("positive", "neutral", "negative", "mixed"):
                sentiment = "unknown"
            return {
                "sentiment": sentiment,
                "confidence": float(data.get("confidence", 0.0)),
                "reasoning": data.get("reasoning", ""),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse sentiment output: %s", e)
            return self._default()

    def _default(self) -> dict[str, Any]:
        return {"sentiment": "unknown", "confidence": 0.0, "reasoning": ""}
