from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceRead
from app.services.adb_watcher import ADBEngine, adb_engine
from app.services.event_bus import EventBus, event_bus
from app.services.event_bus.event_types import (
    DeviceConnectedEvent,
    DeviceDisconnectedEvent,
    DevicesSyncedEvent,
)

logger = logging.getLogger(__name__)

ADB_STATE_MAP: dict[str, tuple[str, bool]] = {
    "device": ("connected", True),
    "unauthorized": ("unauthorized", False),
    "offline": ("offline", False),
    "no permissions": ("unauthorized", False),
}


def map_adb_state(adb_state: str) -> tuple[str, bool]:
    return ADB_STATE_MAP.get(adb_state.strip().lower(), ("disconnected", False))


@dataclass
class DeviceSyncResult:
    adb_devices_found: int = 0
    connected_count: int = 0
    total_registered: int = 0
    updated: int = 0
    disconnected: int = 0
    connected: int = 0
    devices: list[DeviceRead] = field(default_factory=list)


class DeviceSyncService:
    """Reconcile database device records with live `adb devices -l` output."""

    def __init__(self, adb: ADBEngine, bus: EventBus) -> None:
        self.adb = adb
        self.bus = bus

    async def sync(self, db: Session) -> DeviceSyncResult:
        result = DeviceSyncResult()
        now = datetime.now(UTC)
        repo = DeviceRepository(db)

        if not self.adb.is_server_running:
            try:
                await self.adb.start_server()
            except Exception as exc:
                logger.warning("ADB server unavailable during sync: %s", exc)
                return await self._mark_all_disconnected(repo, result, now, reason="adb_unavailable")

        try:
            adb_devices = await self.adb.list_devices()
        except Exception as exc:
            logger.error("ADB list_devices failed during sync: %s", exc)
            return await self._mark_all_disconnected(repo, result, now, reason="adb_list_failed")

        adb_by_serial = {d.serial: d for d in adb_devices}
        result.adb_devices_found = len(adb_devices)
        registered = repo.get_all(limit=500, order_by="id", order_desc=False)
        seen_serials: set[str] = set()

        for serial, adb_dev in adb_by_serial.items():
            seen_serials.add(serial)
            status, is_connected = map_adb_state(adb_dev.state)
            existing = repo.get_by_serial(serial)
            prev_connected = bool(existing and existing.is_connected)

            if existing:
                repo.update(
                    existing.id,
                    is_connected=is_connected,
                    status=status,
                    adb_status=adb_dev.state,
                    manufacturer=adb_dev.manufacturer or existing.manufacturer,
                    model=adb_dev.model or existing.model,
                    android_version=adb_dev.android_version or existing.android_version,
                    last_seen=now,
                )
                result.updated += 1
                device_id = existing.id
            elif is_connected:
                created = repo.create(
                    device_name=f"Android Device ({serial[:8]}...)",
                    serial_number=serial,
                    manufacturer=adb_dev.manufacturer,
                    model=adb_dev.model,
                    android_version=adb_dev.android_version,
                    is_connected=True,
                    status=status,
                    adb_status=adb_dev.state,
                    last_seen=now,
                    heartbeat_at=now,
                )
                device_id = created.id
                result.connected += 1
                try:
                    full_info = await self.adb.get_device_info(serial)
                    new_name = f"{full_info.manufacturer or 'Android'} {full_info.model or ''}".strip()
                    if not new_name or new_name == "Android":
                        new_name = f"Android Device ({serial[:8]}...)"
                    repo.update(
                        created.id,
                        manufacturer=full_info.manufacturer or None,
                        model=full_info.model or None,
                        android_version=full_info.android_version or None,
                        battery_level=full_info.battery_level if full_info.battery_level >= 0 else None,
                        charging=full_info.charging,
                        screen_state=full_info.screen_state if full_info.screen_state != "unknown" else None,
                        device_ip=full_info.device_ip or None,
                        device_name=new_name,
                    )
                except Exception:
                    logger.debug("Could not fetch full info for %s during sync", serial)
                await self._emit_connected(serial, adb_dev, device_id)
            else:
                new_name = f"{adb_dev.manufacturer or 'Android'} {adb_dev.model or ''}".strip()
                if not new_name or new_name == "Android":
                    new_name = f"Android Device ({serial[:8]}...)"
                created = repo.create(
                    device_name=new_name,
                    serial_number=serial,
                    manufacturer=adb_dev.manufacturer,
                    model=adb_dev.model,
                    android_version=adb_dev.android_version,
                    is_connected=False,
                    status=status,
                    adb_status=adb_dev.state,
                    last_seen=now,
                )
                device_id = created.id
                result.updated += 1

            if existing and prev_connected and not is_connected:
                result.disconnected += 1
                await self._emit_disconnected(serial, device_id)
            elif existing and not prev_connected and is_connected:
                result.connected += 1
                await self._emit_connected(serial, adb_dev, device_id)

        for db_device in registered:
            serial = db_device.serial_number
            if not serial:
                if db_device.is_connected:
                    repo.update(
                        db_device.id,
                        is_connected=False,
                        status="disconnected",
                        adb_status="missing_serial",
                        last_seen=now,
                    )
                    result.disconnected += 1
                    result.updated += 1
                    await self._emit_disconnected("", db_device.id)
                continue

            if serial in seen_serials:
                continue

            if db_device.is_connected or db_device.status != "disconnected":
                repo.update(
                    db_device.id,
                    is_connected=False,
                    status="disconnected",
                    adb_status="absent",
                    last_seen=now,
                )
                result.disconnected += 1
                result.updated += 1
                await self._emit_disconnected(serial, db_device.id)

        refreshed = repo.get_all(limit=500, order_by="created_at", order_desc=True)
        result.devices = [DeviceRead.model_validate(d) for d in refreshed]
        result.connected_count = sum(1 for d in refreshed if d.is_connected)
        result.total_registered = len(refreshed)

        await self.bus.publish(
            DevicesSyncedEvent(
                data={
                    "connected_count": result.connected_count,
                    "total_count": result.total_registered,
                    "adb_devices_found": result.adb_devices_found,
                    "updated": result.updated,
                    "disconnected": result.disconnected,
                    "connected": result.connected,
                    "synced_at": now.isoformat(),
                }
            )
        )
        return result

    async def _mark_all_disconnected(
        self,
        repo: DeviceRepository,
        result: DeviceSyncResult,
        now: datetime,
        reason: str,
    ) -> DeviceSyncResult:
        registered = repo.get_all(limit=500)
        for db_device in registered:
            if db_device.is_connected:
                repo.update(
                    db_device.id,
                    is_connected=False,
                    status="disconnected",
                    adb_status=reason,
                    last_seen=now,
                )
                result.disconnected += 1
                if db_device.serial_number:
                    await self._emit_disconnected(db_device.serial_number, db_device.id)
        refreshed = repo.get_all(limit=500, order_by="created_at", order_desc=True)
        result.devices = [DeviceRead.model_validate(d) for d in refreshed]
        result.total_registered = len(refreshed)
        result.connected_count = 0
        await self.bus.publish(
            DevicesSyncedEvent(
                data={
                    "connected_count": 0,
                    "total_count": result.total_registered,
                    "reason": reason,
                    "synced_at": now.isoformat(),
                }
            )
        )
        return result

    async def _emit_connected(self, serial: str, adb_dev: object, device_id: int) -> None:
        await self.bus.publish(
            DeviceConnectedEvent(
                device_id=device_id,
                serial=serial,
                manufacturer=getattr(adb_dev, "manufacturer", "") or "",
                model=getattr(adb_dev, "model", "") or "",
                data={"serial": serial, "device_id": device_id},
            )
        )

    async def _emit_disconnected(self, serial: str, device_id: int) -> None:
        await self.bus.publish(
            DeviceDisconnectedEvent(
                device_id=device_id,
                serial=serial,
                data={"serial": serial, "device_id": device_id},
            )
        )


device_sync_service = DeviceSyncService(adb_engine, event_bus)
