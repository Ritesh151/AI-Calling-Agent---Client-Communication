from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.services.adb_manager import ADBManager
from app.services.device_status import DeviceStatusService

logger = logging.getLogger(__name__)


async def run_heartbeat_worker() -> None:
    db = SessionLocal()
    try:
        adb = ADBManager()
        status_service = DeviceStatusService(db, adb)
        await status_service.start_heartbeat()
        logger.info("Device heartbeat worker started")

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await status_service.stop_heartbeat()
    finally:
        db.close()


def start_heartbeat_worker() -> None:
    asyncio.run(run_heartbeat_worker())
