from __future__ import annotations

import logging

from app.services.adb_watcher import adb_engine
from app.services.device_heartbeat import DeviceHeartbeatService
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class DeviceHeartbeatWorker:
    def __init__(self) -> None:
        self._service: DeviceHeartbeatService | None = None

    async def start(self) -> None:
        self._service = DeviceHeartbeatService(adb_engine, event_bus)
        await self._service.start()
        logger.info("Device heartbeat worker started")

    async def stop(self) -> None:
        if self._service:
            await self._service.stop()
        logger.info("Device heartbeat worker stopped")

    @property
    def is_running(self) -> bool:
        return self._service is not None and self._service._running
