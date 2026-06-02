from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.device import Device
from app.db.models.device_capability import DeviceCapability
from app.repositories.device_repository import DeviceRepository
from app.services.compatibility.diagnostics.stress_test_service import (
    StressTestService,
)
from app.services.event_bus import Event, EventPriority, event_bus

logger = logging.getLogger(__name__)


class StressTestWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Stress test worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stress test worker stopped")

    async def _run(self) -> None:
        await asyncio.sleep(60)
        while self._running:
            try:
                await self._run_stress_tests()
            except Exception as e:
                logger.error("Stress test worker error: %s", e)
            await asyncio.sleep(86400)

    async def _run_stress_tests(self) -> None:
        db = SessionLocal()
        try:
            repo = DeviceRepository(db)
            devices = repo.get_all(limit=10)
            for device in devices:
                if device.id is None:
                    continue
                capability = db.query(DeviceCapability).filter(
                    DeviceCapability.device_id == device.id
                ).first()
                if capability and capability.capability_score and capability.capability_score >= 50:
                    try:
                        service = StressTestService(SessionLocal)
                        result = await service.run_stress_test(
                            device_id=device.id,
                            duration_hours=1,
                            operations_per_minute=10,
                        )
                        await event_bus.publish(Event(
                            type="stress_test_completed",
                            data={
                                "device_id": device.id,
                                "stability": result.connection_stability,
                                "failure_rate": result.failure_rate,
                                "certificate_retained": result.certificate_retained,
                            },
                            priority=EventPriority.NORMAL,
                        ))
                        logger.info("Stress test completed for device %d", device.id)
                    except Exception as e:
                        logger.warning("Stress test failed for device %d: %s", device.id, e)
        finally:
            db.close()
