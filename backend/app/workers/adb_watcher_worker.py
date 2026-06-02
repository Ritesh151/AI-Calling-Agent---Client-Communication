from __future__ import annotations

import asyncio
import logging

from app.services.adb_watcher import ADBEngine, adb_engine
from app.services.adb_watcher.adb_watcher_service import ADBWatcherService
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class ADBWatcherWorker:
    def __init__(self) -> None:
        self._service: ADBWatcherService | None = None

    async def start(self) -> None:
        self._service = ADBWatcherService(adb_engine, event_bus)
        await self._service.start()
        logger.info("ADB watcher worker started")

    async def stop(self) -> None:
        if self._service:
            await self._service.stop()
        logger.info("ADB watcher worker stopped")

    @property
    def is_running(self) -> bool:
        return self._service is not None and self._service._running
