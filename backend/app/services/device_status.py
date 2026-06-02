from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.adb_manager import ADBManager
from app.services.device_registry import DeviceRegistryService
from app.services.websocket import ws_manager

logger = logging.getLogger(__name__)


class DeviceStatusService:
    def __init__(self, db: Session, adb_manager: ADBManager) -> None:
        self.adb = adb_manager
        self.registry = DeviceRegistryService(db)
        self._running = False
        self._task: asyncio.Task | None = None
        # Track previous connection state to detect changes
        self._prev_connection_status: dict[str, bool] = {}

    async def start_heartbeat(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Device heartbeat service started")

    async def stop_heartbeat(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Device heartbeat service stopped")

    async def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                if not self.adb.is_connected:
                    await self.adb.connect()

                devices = await self.adb.list_devices()
                online_serials = {d.serial for d in devices if d.state == "device"}

                for device in devices:
                    self.registry.register_or_update(
                        serial=device.serial,
                        manufacturer=device.manufacturer,
                        model=device.model,
                        android_version=device.android_version,
                        android_id=device.android_id,
                        is_connected=(device.state == "device"),
                    )

                logger.debug(
                    "Heartbeat cycle completed",
                    extra={"devices_found": len(devices), "online": len(online_serials)},
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(settings.DEVICE_HEARTBEAT_INTERVAL_SECONDS)

    async def check_device_status(self, serial: str) -> dict:
        if not self.adb.is_connected:
            await self.adb.connect()

        is_online = await self.adb.is_device_online(serial)
        device_info = await self.adb.get_device_info(serial)

        return {
            "serial": serial,
            "is_online": is_online,
            "manufacturer": device_info.manufacturer,
            "model": device_info.model,
            "android_version": device_info.android_version,
            "state": device_info.state,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    @property
    def is_running(self) -> bool:
        return self._running
