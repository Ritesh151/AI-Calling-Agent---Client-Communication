from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.services.compatibility.device_profiles.certification_service import (
    CertificationService,
)
from app.services.event_bus import Event, EventPriority, event_bus

logger = logging.getLogger(__name__)


class CertificationWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Certification worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Certification worker stopped")

    async def _run(self) -> None:
        await asyncio.sleep(120)
        while self._running:
            try:
                await self._recertify()
            except Exception as e:
                logger.error("Certification worker error: %s", e)
            await asyncio.sleep(43200)

    async def _recertify(self) -> None:
        db = SessionLocal()
        try:
            service = CertificationService(db)
            results = service.recertify_all(limit=100)
            for r in results:
                await event_bus.publish(Event(
                    type="device_certified",
                    data={"device_id": r["device_id"], "level": r["level"], "score": r["score"]},
                    priority=EventPriority.NORMAL,
                ))
            logger.info("Recertified %d devices", len(results))
        finally:
            db.close()
