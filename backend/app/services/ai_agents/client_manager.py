from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_agents.base_agent import BaseAIAgent

CLIENT_SYSTEM = """You are an AI Client Manager. Talk with clients professionally.
Ask clarifying questions for missing requirements. Generate BRD, SRS, technical design,
user stories, acceptance criteria, sprint tasks, roadmap, milestones, budget, delivery plan.
Output structured JSON with documents and open_questions[]."""


class AIClientManager(BaseAIAgent):
    agent_type = "client_manager"

    async def process(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        project_id = (context or {}).get("project_id")
        self._log_conversation(project_id, "user", message, context)

        response = await self._llm_complete(
            CLIENT_SYSTEM,
            f"Context: {context}\n\nClient message: {message}",
        )
        self._log_conversation(project_id, "assistant", response)

        return {
            "agent": self.agent_type,
            "response": response,
            "deliverables": [
                "brd",
                "srs",
                "technical_design",
                "user_stories",
                "acceptance_criteria",
                "sprint_tasks",
                "roadmap",
                "milestones",
                "budget_estimate",
                "delivery_plan",
            ],
        }


def get_client_manager(db: Session) -> AIClientManager:
    return AIClientManager(db)
