from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.services.adb_watcher import ADBEngine, adb_engine
from app.services.event_bus import EventBus, event_bus
from app.services.event_bus.event_types import (
    ADBStatusChangedEvent,
    DeviceConnectedEvent,
    DeviceDisconnectedEvent,
)

logger = logging.getLogger(__name__)


class ADBWatcherService:
    def __init__(self, adb_engine: ADBEngine, event_bus: EventBus) -> None:
        self.adb = adb_engine
        self.event_bus = event_bus
        self._running = False
        self._task: asyncio.Task | None = None
        self._known_devices: set[str] = set()
        self._last_adb_status: str = "unknown"

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info("ADB watcher started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ADB watcher stopped")

    async def _watch_loop(self) -> None:
        while self._running:
            try:
                if not self.adb.is_server_running:
                    try:
                        await self.adb.start_server()
                        self._update_adb_status("connected")
                    except Exception as e:
                        self._update_adb_status("error", str(e))
                        await asyncio.sleep(5)
                        continue

                devices = await self.adb.list_devices()
                current_serials = {d.serial for d in devices if d.state == "device"}

                newly_connected = current_serials - self._known_devices
                newly_disconnected = self._known_devices - current_serials

                for serial in newly_connected:
                    await self._handle_device_connected(serial, devices)

                for serial in newly_disconnected:
                    await self._handle_device_disconnected(serial)

                self._known_devices = current_serials

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("ADB watcher error: %s", e)
                self._update_adb_status("error", str(e))

            await asyncio.sleep(settings.DEVICE_WATCH_INTERVAL_SECONDS)

    async def _handle_device_connected(self, serial: str, devices: list) -> None:
        device_info = None
        for d in devices:
            if d.serial == serial:
                device_info = d
                break

        event = DeviceConnectedEvent(
            device_id=hash(serial),
            serial=serial,
            manufacturer=device_info.manufacturer if device_info else "",
            model=device_info.model if device_info else "",
            data={
                "serial": serial,
                "connected_at": datetime.now(UTC).isoformat(),
            },
        )
        await self.event_bus.publish(event)
        logger.info("Device connected: %s", serial)

    async def _handle_device_disconnected(self, serial: str) -> None:
        event = DeviceDisconnectedEvent(
            device_id=hash(serial),
            serial=serial,
            data={
                "serial": serial,
                "disconnected_at": datetime.now(UTC).isoformat(),
            },
        )
        await self.event_bus.publish(event)
        logger.info("Device disconnected: %s", serial)

    def _update_adb_status(self, status: str, error: str | None = None) -> None:
        if self._last_adb_status != status:
            old_status = self._last_adb_status
            self._last_adb_status = status
            asyncio.ensure_future(
                self.event_bus.publish(
                    ADBStatusChangedEvent(
                        old_status=old_status,
                        new_status=status,
                        data={"status": status, "error": error},
                    )
                )
            )
