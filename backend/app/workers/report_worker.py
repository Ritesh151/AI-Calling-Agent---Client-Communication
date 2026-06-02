from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.services.reporting.report_service import ReportService

logger = logging.getLogger(__name__)


class ReportWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Report worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Report worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._generate_daily()
            except Exception as e:
                logger.error("Report worker error: %s", e)
            await asyncio.sleep(86400)

    def _generate_daily(self) -> None:
        db = SessionLocal()
        try:
            service = ReportService(db)
            now = datetime.now(timezone.utc)
            today_str = now.strftime("%Y-%m-%d")
            week_ago = now.strftime("%Y-%m-%d")

            result = service.generate_report(
                report_type="call_summary",
                fmt="csv",
            )
            logger.info("Daily report generated: %s", result.get("file_path", ""))
        finally:
            db.close()
