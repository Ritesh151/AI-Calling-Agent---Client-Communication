from __future__ import annotations

import logging

from app.services.adb_watcher import adb_engine
from app.services.call_detector import CallDetectionEngine
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class CallDetectionWorker:
    def __init__(self) -> None:
        self._engine: CallDetectionEngine | None = None

    async def start(self) -> None:
        self._engine = CallDetectionEngine(adb_engine, event_bus)
        await self._engine.start()
        logger.info("Call detection worker started")

    async def stop(self) -> None:
        if self._engine:
            await self._engine.stop()
        logger.info("Call detection worker stopped")

    @property
    def is_running(self) -> bool:
        return self._engine is not None and self._engine._running
