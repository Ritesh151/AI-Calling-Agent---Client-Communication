from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.recovery_log_model import RecoveryLog
from app.repositories.recovery_log_repository import RecoveryLogRepository
from app.services.compatibility.recovery_engine.recovery_engine import RecoveryEngine

logger = logging.getLogger(__name__)


class RecoveryWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None
        self._processed_ids: set[int] = set()

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Recovery worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Recovery worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._process_failed()
            except Exception as e:
                logger.error("Recovery worker error: %s", e)
            await asyncio.sleep(60)

    async def _process_failed(self) -> None:
        db = SessionLocal()
        try:
            repo = RecoveryLogRepository(db)
            failed = repo.get_failed_recoveries()
            for log in failed:
                if log.id is None or log.id in self._processed_ids:
                    continue
                self._processed_ids.add(log.id)
                try:
                    engine = RecoveryEngine(db)
                    result = await engine.attempt_recovery(log.device_id, log.failure_type)
                    if result.get("success"):
                        logger.info("Recovery succeeded for device %d (log %d)", log.device_id, log.id)
                    else:
                        logger.warning("Recovery failed for device %d (log %d)", log.device_id, log.id)
                except Exception as e:
                    logger.error("Recovery attempt error for device %d: %s", log.device_id, e)
            if len(self._processed_ids) > 1000:
                self._processed_ids.clear()
        finally:
            db.close()
