from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceRead


class DeviceRegistryService:
    def __init__(self, db: Session) -> None:
        self.device_repo = DeviceRepository(db)

    def register_or_update(
        self,
        serial: str,
        manufacturer: str = "",
        model: str = "",
        android_version: str = "",
        android_id: str = "",
        device_name: str | None = None,
        is_connected: bool = False,
    ) -> DeviceRead:
        existing = self.device_repo.get_by_serial(serial)

        if existing:
            device = self.device_repo.update(
                existing.id,
                manufacturer=manufacturer or existing.manufacturer,
                model=model or existing.model,
                android_version=android_version or existing.android_version,
                android_id=android_id or existing.android_id,
                is_connected=is_connected,
                status="connected" if is_connected else "disconnected",
                last_seen=datetime.now(UTC),
            )
        else:
            name = device_name or f"Android Device ({serial[:8]}...)"
            device = self.device_repo.create(
                device_name=name,
                serial_number=serial,
                manufacturer=manufacturer,
                model=model,
                android_version=android_version,
                android_id=android_id,
                is_connected=is_connected,
                status="connected" if is_connected else "disconnected",
                last_seen=datetime.now(UTC),
            )

        return DeviceRead.model_validate(device)

    def unregister_device(self, device_id: int) -> None:
        self.device_repo.update(
            device_id,
            is_connected=False,
            status="disconnected",
            last_seen=datetime.now(UTC),
        )

    def update_connection_status(self, serial: str, is_connected: bool) -> DeviceRead | None:
        existing = self.device_repo.get_by_serial(serial)
        if existing:
            device = self.device_repo.update(
                existing.id,
                is_connected=is_connected,
                status="connected" if is_connected else "disconnected",
                last_seen=datetime.now(UTC),
            )
            return DeviceRead.model_validate(device)
        return None

    def get_registered_device(self, serial: str) -> DeviceRead | None:
        device = self.device_repo.get_by_serial(serial)
        if device:
            return DeviceRead.model_validate(device)
        return None
