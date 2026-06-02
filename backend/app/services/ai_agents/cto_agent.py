from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_agents.base_agent import BaseAIAgent

CTO_SYSTEM = """You are an AI CTO. Review requirements and produce architecture,
database design, API specs, frontend/backend/AI/testing/deployment tasks, documentation.
Output structured JSON with architecture, apis[], db_schema, task_breakdown."""


class AICTOAgent(BaseAIAgent):
    agent_type = "cto"

    async def process(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        project_id = (context or {}).get("project_id")
        self._log_conversation(project_id, "user", message, context)

        response = await self._llm_complete(
            CTO_SYSTEM,
            f"Requirements/context: {context}\n\nRequest: {message}",
        )
        self._log_conversation(project_id, "assistant", response)

        return {
            "agent": self.agent_type,
            "response": response,
            "outputs": [
                "architecture",
                "database_design",
                "api_specs",
                "frontend_tasks",
                "backend_tasks",
                "ai_tasks",
                "testing_tasks",
                "deployment_tasks",
                "documentation",
            ],
        }


def get_cto_agent(db: Session) -> AICTOAgent:
    return AICTOAgent(db)
