from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.device import Device
from app.repositories.device_repository import DeviceRepository
from app.services.compatibility.diagnostics.diagnostics_service import (
    DiagnosticsService,
)
from app.services.event_bus import Event, EventPriority, event_bus

logger = logging.getLogger(__name__)


class DiagnosticsWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Diagnostics worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Diagnostics worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._run_diagnostics()
            except Exception as e:
                logger.error("Diagnostics worker error: %s", e)
            await asyncio.sleep(3600)

    async def _run_diagnostics(self) -> None:
        db = SessionLocal()
        try:
            repo = DeviceRepository(db)
            devices = repo.get_all(limit=50)
            for device in devices:
                if device.id is None:
                    continue
                try:
                    service = DiagnosticsService(db)
                    diag = await service.run_diagnostics(device.id)
                    await event_bus.publish(Event(
                        type="diagnostic_generated",
                        data={"device_id": device.id, "score": diag.get("capability_score", 0)},
                        priority=EventPriority.NORMAL,
                    ))
                    logger.info("Diagnostics complete for device %d", device.id)
                except Exception as e:
                    logger.warning("Diagnostics failed for device %d: %s", device.id, e)
        finally:
            db.close()
