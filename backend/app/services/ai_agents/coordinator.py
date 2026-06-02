from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_agents.base_agent import BaseAIAgent

COORDINATOR_SYSTEM = """You are an AI Project Coordinator for software delivery.
Capabilities: requirement gathering, technical analysis, estimation, sprint planning,
task creation, developer assignment, progress tracking, bug tracking, release planning,
risk detection, client reporting, meeting summaries, timeline forecasting.
Respond with structured JSON: analysis, risks, tasks[], sprints[], estimates."""


class AIProjectCoordinator(BaseAIAgent):
    agent_type = "project_coordinator"

    async def process(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        project_id = (context or {}).get("project_id")
        self._log_conversation(project_id, "user", message, context)

        response = await self._llm_complete(
            COORDINATOR_SYSTEM,
            f"Client/project context: {context}\n\nRequest: {message}",
        )
        self._log_conversation(project_id, "assistant", response)

        return {
            "agent": self.agent_type,
            "response": response,
            "capabilities": [
                "client_chat",
                "requirement_gathering",
                "technical_analysis",
                "project_estimation",
                "sprint_planning",
                "task_creation",
                "developer_assignment",
                "progress_tracking",
                "bug_tracking",
                "release_planning",
                "risk_detection",
                "client_reporting",
                "meeting_summaries",
                "timeline_forecasting",
            ],
        }


def get_coordinator(db: Session) -> AIProjectCoordinator:
    return AIProjectCoordinator(db)
