from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.project_management import BugReport
from app.services.adb_watcher import adb_engine
from app.services.ai_agents.base_agent import BaseAIAgent
from app.services.device_sync import device_sync_service

logger = logging.getLogger(__name__)


class AIQAAgent(BaseAIAgent):
    agent_type = "qa"

    async def process(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        findings = await self.run_health_scan(context)
        return {
            "agent": self.agent_type,
            "findings": findings,
            "message": message,
        }

    async def run_health_scan(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        project_id = (context or {}).get("project_id")
        findings: list[dict[str, Any]] = []

        try:
            adb_health = await adb_engine.health_check()
            if not adb_health.get("is_healthy"):
                findings.append(self._finding("adb", "high", "ADB unhealthy", str(adb_health)))
        except Exception as exc:
            findings.append(self._finding("adb", "critical", "ADB health check failed", str(exc)))

        try:
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                sync_result = await device_sync_service.sync(db)
                if sync_result.disconnected > 0:
                    findings.append(
                        self._finding(
                            "devices",
                            "medium",
                            f"{sync_result.disconnected} stale connected device(s) corrected",
                            f"connected={sync_result.connected_count}",
                        )
                    )
            finally:
                db.close()
        except Exception as exc:
            findings.append(self._finding("database", "high", "Device sync failed", str(exc)))

        try:
            from sqlalchemy import text
            from app.core.database import SessionLocal

            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as exc:
            findings.append(self._finding("database", "critical", "Database unreachable", str(exc)))

        for item in findings:
            bug = BugReport(
                project_id=project_id,
                title=item["title"],
                description=item.get("detail"),
                severity=item["severity"],
                category=item["category"],
                status="open",
                detected_by=self.agent_type,
            )
            self.db.add(bug)
        if findings:
            self.db.commit()

        return findings

    def _finding(
        self, category: str, severity: str, title: str, detail: str
    ) -> dict[str, Any]:
        return {
            "category": category,
            "severity": severity,
            "title": title,
            "detail": detail,
        }


def get_qa_agent(db: Session) -> AIQAAgent:
    return AIQAAgent(db)
