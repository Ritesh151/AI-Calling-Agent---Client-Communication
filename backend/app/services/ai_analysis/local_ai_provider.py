from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.services.ai_analysis.ai_provider import AIProvider, AIAnalysisResult

logger = logging.getLogger(__name__)


class LocalAIProvider(AIProvider):
    def __init__(self) -> None:
        self._client: Any = None
        self._model = settings.AI_ANALYSIS_LOCAL_MODEL or "llama3"

    def analyze(self, prompt: str, system_prompt: str | None = None, max_tokens: int | None = None) -> AIAnalysisResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            import ollama
            start = time.monotonic()
            response = ollama.chat(
                model=self._model,
                messages=messages,
                options={"temperature": 0.1, "num_predict": max_tokens or 2048},
            )
            content = response["message"]["content"]
            return AIAnalysisResult(
                success=True,
                content=content,
                model=self._model,
            )
        except ImportError:
            return self._http_fallback(prompt, system_prompt, max_tokens)
        except Exception as e:
            logger.error("Local AI failed: %s", e)
            return AIAnalysisResult(success=False, error=str(e))

    def structured_analysis(self, prompt: str, output_format: dict, system_prompt: str | None = None) -> AIAnalysisResult:
        sys_prompt = system_prompt or "Respond only with valid JSON."
        sys_prompt += f"\n\nJSON schema: {json.dumps(output_format)}"
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
            import ollama
            return True
        except ImportError:
            return bool(settings.AI_ANALYSIS_API_BASE)

    def _http_fallback(self, prompt: str, system_prompt: str | None = None, max_tokens: int | None = None) -> AIAnalysisResult:
        import httpx
        api_base = settings.AI_ANALYSIS_API_BASE or "http://localhost:11434/api/generate"
        try:
            response = httpx.post(
                api_base,
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "system": system_prompt or "",
                    "options": {"temperature": 0.1, "num_predict": max_tokens or 2048},
                },
                timeout=60,
            )
            if response.status_code == 200:
                return AIAnalysisResult(success=True, content=response.text, model=self._model)
            return AIAnalysisResult(success=False, error=f"HTTP {response.status_code}")
        except Exception as e:
            return AIAnalysisResult(success=False, error=str(e))

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
