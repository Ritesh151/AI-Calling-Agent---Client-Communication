from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.models.device import Device
from app.db.models.device_metric import DeviceMetric
from app.repositories.device_repository import DeviceRepository
from app.services.adb_watcher import ADBEngine, adb_engine
from app.services.device_sync import DeviceSyncService
from app.services.event_bus import EventBus, event_bus
from app.services.event_bus.event_types import (
    DeviceHeartbeatEvent,
    DeviceMetricsUpdatedEvent,
)

logger = logging.getLogger(__name__)


class DeviceHeartbeatService:
    def __init__(self, adb_engine: ADBEngine, event_bus: EventBus) -> None:
        self.adb = adb_engine
        self.event_bus = event_bus
        self._sync = DeviceSyncService(adb_engine, event_bus)
        self._running = False
        self._task: asyncio.Task | None = None
        self._metrics_buffer: list[dict[str, Any]] = []

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Device heartbeat service started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush_metrics()
        logger.info("Device heartbeat service stopped")

    async def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                if not self.adb.is_server_running:
                    await asyncio.sleep(5)
                    continue

                db_sync = SessionLocal()
                try:
                    await self._sync.sync(db_sync)
                finally:
                    db_sync.close()

                devices = await self.adb.list_devices()
                for dev in devices:
                    if dev.state != "device":
                        continue
                    try:
                        await self._process_device_heartbeat(dev.serial)
                    except Exception as e:
                        logger.debug(
                            "Heartbeat error for %s: %s", dev.serial, e
                        )

                if self._metrics_buffer:
                    await self._flush_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat loop error: %s", e)

            await asyncio.sleep(settings.DEVICE_HEARTBEAT_INTERVAL_SECONDS)

    async def _process_device_heartbeat(self, serial: str) -> None:
        info = await self.adb.get_device_info(serial)
        now = datetime.now(UTC)

        db = SessionLocal()
        try:
            repo = DeviceRepository(db)
            device = repo.get_by_serial(serial)
            if device:
                new_name = device.device_name
                if info.manufacturer or info.model:
                    candidate = f"{info.manufacturer or 'Android'} {info.model or ''}".strip()
                    if candidate and candidate != "Android":
                        new_name = candidate
                repo.update(
                    device.id,
                    is_connected=True,
                    status="connected",
                    last_seen=now,
                    heartbeat_at=now,
                    manufacturer=info.manufacturer or device.manufacturer,
                    model=info.model or device.model,
                    android_version=info.android_version or device.android_version,
                    device_name=new_name,
                    battery_level=info.battery_level if info.battery_level >= 0 else device.battery_level,
                    charging=info.charging if info.charging is not None else device.charging,
                    screen_state=info.screen_state if info.screen_state != "unknown" else device.screen_state,
                    device_ip=info.device_ip or device.device_ip,
                )
            else:
                new_name = f"{info.manufacturer or 'Android'} {info.model or ''}".strip()
                if not new_name or new_name == "Android":
                    new_name = f"Android Device ({serial[:8]}...)"
                device = repo.create(
                    device_name=new_name,
                    serial_number=serial,
                    manufacturer=info.manufacturer,
                    model=info.model,
                    android_version=info.android_version,
                    is_connected=True,
                    status="connected",
                    last_seen=now,
                    heartbeat_at=now,
                    battery_level=info.battery_level if info.battery_level >= 0 else None,
                    charging=info.charging,
                    screen_state=info.screen_state if info.screen_state != "unknown" else None,
                )

            metric = DeviceMetric(
                device_id=device.id,
                battery_level=info.battery_level if info.battery_level >= 0 else None,
                charging=info.charging,
                screen_state=info.screen_state if info.screen_state != "unknown" else None,
                usb_connected=info.usb_connected,
                captured_at=now,
            )
            db.add(metric)
            db.commit()

            await self.event_bus.publish(
                DeviceHeartbeatEvent(
                    device_id=device.id,
                    battery_level=info.battery_level,
                    charging=info.charging,
                    screen_state=info.screen_state,
                    is_online=True,
                    data={
                        "serial": serial,
                        "device_id": device.id,
                        "timestamp": now.isoformat(),
                    },
                )
            )

            await self.event_bus.publish(
                DeviceMetricsUpdatedEvent(
                    device_id=device.id,
                    battery_level=info.battery_level,
                    charging=info.charging,
                    screen_state=info.screen_state,
                    data={
                        "serial": serial,
                        "battery": info.battery_level,
                        "charging": info.charging,
                        "screen": info.screen_state,
                    },
                )
            )

        except Exception as e:
            logger.error("Heartbeat DB update failed for %s: %s", serial, e)
            db.rollback()
        finally:
            db.close()

    async def _flush_metrics(self) -> None:
        if not self._metrics_buffer:
            return
        buffer = self._metrics_buffer.copy()
        self._metrics_buffer.clear()

        db = SessionLocal()
        try:
            for metric_data in buffer:
                metric = DeviceMetric(**metric_data)
                db.add(metric)
            db.commit()
        except Exception as e:
            logger.error("Failed to flush metrics: %s", e)
            db.rollback()
        finally:
            db.close()
