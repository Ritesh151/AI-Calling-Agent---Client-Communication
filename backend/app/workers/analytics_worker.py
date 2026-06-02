from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.analytics_engine.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class AnalyticsWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Analytics worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Analytics worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._compute_analytics()
            except Exception as e:
                logger.error("Analytics worker error: %s", e)
            await asyncio.sleep(3600)

    def _compute_analytics(self) -> None:
        db = SessionLocal()
        try:
            service = AnalyticsService(db)
            dash = service.get_dashboard(days=30)
            logger.info(
                "Analytics computed: %d calls, %d answered, %.1f%% recording rate",
                dash["metrics"]["total_calls"],
                dash["metrics"]["answered_calls"],
                dash["metrics"]["recording_success_rate"],
            )
        finally:
            db.close()
