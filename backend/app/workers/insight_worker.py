from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.insights.insight_service import InsightService

logger = logging.getLogger(__name__)


class InsightWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Insight worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Insight worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._generate()
            except Exception as e:
                logger.error("Insight worker error: %s", e)
            await asyncio.sleep(settings.INSIGHT_SCHEDULE_HOURS * 3600)

    def _generate(self) -> None:
        db = SessionLocal()
        try:
            service = InsightService(db)
            insights = service.generate_insights()
            if insights:
                logger.info("Generated %d insights", len(insights))
                for ins in insights:
                    logger.info("Insight: %s", ins["content"])
            else:
                logger.debug("No new insights generated")
        finally:
            db.close()
