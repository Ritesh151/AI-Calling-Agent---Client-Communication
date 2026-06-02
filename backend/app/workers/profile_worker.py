from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.device import Device
from app.repositories.device_repository import DeviceRepository
from app.services.compatibility.device_profiles.profile_service import (
    DeviceProfileService,
)

logger = logging.getLogger(__name__)


class ProfileWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Profile worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Profile worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._process_pending()
            except Exception as e:
                logger.error("Profile worker error: %s", e)
            await asyncio.sleep(600)

    async def _process_pending(self) -> None:
        db = SessionLocal()
        try:
            repo = DeviceRepository(db)
            devices = repo.get_all(limit=50)
            for device in devices:
                if device.id is None:
                    continue
                try:
                    service = DeviceProfileService(db)
                    service.get_or_create_profile(device.id)
                    logger.info("Profile generated for device %d", device.id)
                except Exception as e:
                    logger.warning("Profile generation failed for device %d: %s", device.id, e)
        finally:
            db.close()
