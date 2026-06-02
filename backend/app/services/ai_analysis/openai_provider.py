from __future__ import annotations

import json
import logging
import time

from app.core.config import settings
from app.services.ai_analysis.ai_provider import AIProvider, AIAnalysisResult

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self._client = None
        self._model = settings.AI_ANALYSIS_MODEL or "gpt-4o-mini"

    def analyze(self, prompt: str, system_prompt: str | None = None, max_tokens: int | None = None) -> AIAnalysisResult:
        client = self._get_client()
        start = time.monotonic()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens or 2048,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage.__dict__ if response.usage else {}
            return AIAnalysisResult(
                success=True,
                content=content,
                token_usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                model=self._model,
            )
        except Exception as e:
            logger.error("OpenAI analysis failed: %s", e)
            return AIAnalysisResult(success=False, error=str(e))

    def structured_analysis(self, prompt: str, output_format: dict, system_prompt: str | None = None) -> AIAnalysisResult:
        sys_prompt = system_prompt or "You are a precise call analysis assistant. Respond only with valid JSON."
        sys_prompt += f"\n\nRespond with a JSON object matching this schema: {json.dumps(output_format)}"
        result = self.analyze(prompt, system_prompt=sys_prompt, max_tokens=4096)
        if result.success and result.content:
            try:
                json_content = self._extract_json(result.content)
                result.content = json.dumps(json_content)
            except (json.JSONDecodeError, ValueError) as e:
                result.success = False
                result.error = f"JSON parse error: {e}"
        return result

    def validate(self) -> bool:
        try:
            import openai
            return bool(settings.AI_ANALYSIS_API_KEY)
        except ImportError:
            return False

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(
                api_key=settings.AI_ANALYSIS_API_KEY,
                base_url=settings.AI_ANALYSIS_API_BASE or None,
            )
        return self._client

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
