from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.project_management import AgentConversation

logger = logging.getLogger(__name__)


class BaseAIAgent(ABC):
    agent_type: str = "base"

    def __init__(self, db: Session) -> None:
        self.db = db

    @abstractmethod
    async def process(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def _log_conversation(
        self,
        project_id: int | None,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = AgentConversation(
            project_id=project_id,
            agent_type=self.agent_type,
            role=role,
            content=content,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.db.add(entry)
        self.db.commit()

    async def _llm_complete(self, system_prompt: str, user_message: str) -> str:
        """Invoke configured AI provider; falls back to structured template when no API key."""
        api_key = settings.AI_ANALYSIS_API_KEY
        if not api_key:
            return self._fallback_response(system_prompt, user_message)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.AI_ANALYSIS_API_BASE or None,
            )
            response = await client.chat.completions.create(
                model=settings.AI_ANALYSIS_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=settings.AI_ANALYSIS_TEMPERATURE,
                max_tokens=settings.AI_ANALYSIS_MAX_TOKENS,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("LLM call failed for %s: %s", self.agent_type, exc)
            return self._fallback_response(system_prompt, user_message)

    def _fallback_response(self, system_prompt: str, user_message: str) -> str:
        return json.dumps(
            {
                "agent": self.agent_type,
                "note": "Configure AI_ANALYSIS_API_KEY for full autonomous responses.",
                "system": system_prompt[:200],
                "input_summary": user_message[:500],
                "suggested_actions": [
                    "Review requirements",
                    "Break down into tasks",
                    "Assign owners",
                ],
            },
            indent=2,
        )
