from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.services.adb_manager import ADBManager, DeviceInfo
from app.services.device_registry import DeviceRegistryService


class DeviceDiscoveryService:
    def __init__(self, db: Session, adb_manager: ADBManager) -> None:
        self.adb = adb_manager
        self.registry = DeviceRegistryService(db)

    async def discover_devices(self) -> list[dict]:
        if not self.adb.is_connected:
            await self.adb.connect()

        devices = await self.adb.list_devices()
        results = []

        for device in devices:
            try:
                registered = self.registry.register_or_update(
                    serial=device.serial,
                    manufacturer=device.manufacturer,
                    model=device.model,
                    android_version=device.android_version,
                    android_id=device.android_id,
                    is_connected=(device.state == "device"),
                )
                results.append(registered.model_dump())
            except Exception:
                results.append(
                    {
                        "serial": device.serial,
                        "error": "Failed to register device",
                    }
                )

        return results

    async def scan_single_device(self, serial: str) -> dict | None:
        if not self.adb.is_connected:
            await self.adb.connect()

        try:
            info = await self.adb.get_device_info(serial)
            registered = self.registry.register_or_update(
                serial=info.serial,
                manufacturer=info.manufacturer,
                model=info.model,
                android_version=info.android_version,
                android_id=info.android_id,
                is_connected=(info.state == "device"),
            )
            return registered.model_dump()
        except Exception as e:
            raise AppException(
                message=f"Failed to scan device {serial}: {str(e)}",
                error_code="DEVICE_SCAN_ERROR",
            )
