from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate


class DeviceService:
    def __init__(self, db: Session) -> None:
        self.device_repo = DeviceRepository(db)

    def register_device(self, request: DeviceCreate) -> DeviceRead:
        if request.serial_number and self.device_repo.get_by_serial(request.serial_number):
            raise ConflictException("Device with this serial number already exists")

        device = self.device_repo.create(
            device_name=request.device_name,
            android_id=request.android_id,
            serial_number=request.serial_number,
            manufacturer=request.manufacturer,
            model=request.model,
            android_version=request.android_version,
            status="disconnected",
            is_connected=False,
            last_seen=datetime.now(UTC),
        )
        return DeviceRead.model_validate(device)

    def get_device(self, device_id: int) -> DeviceRead:
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundException("Device not found")
        return DeviceRead.model_validate(device)

    def get_all_devices(self, skip: int = 0, limit: int = 100) -> list[DeviceRead]:
        devices = self.device_repo.get_all(skip=skip, limit=limit, order_by="created_at", order_desc=True)
        return [DeviceRead.model_validate(d) for d in devices]

    def update_device(self, device_id: int, request: DeviceUpdate) -> DeviceRead:
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundException("Device not found")

        update_data = request.model_dump(exclude_unset=True)
        updated = self.device_repo.update(device_id, **update_data)
        return DeviceRead.model_validate(updated)

    def delete_device(self, device_id: int) -> None:
        if not self.device_repo.delete(device_id):
            raise NotFoundException("Device not found")

    def update_heartbeat(self, device_id: int) -> DeviceRead:
        device = self.device_repo.update_heartbeat(device_id)
        if not device:
            raise NotFoundException("Device not found")
        return DeviceRead.model_validate(device)

    def get_connected_devices(self) -> list[DeviceRead]:
        devices = self.device_repo.get_connected_devices()
        return [DeviceRead.model_validate(d) for d in devices]

    def get_device_count(self) -> int:
        return self.device_repo.count()

    def get_connected_count(self) -> int:
        return self.device_repo.count(is_connected=True)

    def cleanup_stale_devices(self, timeout_seconds: int = 300) -> dict[str, int]:
        """
        Mark devices as offline if not seen for timeout_seconds.
        Delete devices that have been offline for more than retention_days.
        
        Returns dict with counts of devices marked offline and deleted.
        """
        from app.core.config import settings
        
        now = datetime.now(UTC)
        timeout = settings.DEVICE_TIMEOUT_SECONDS or timeout_seconds
        retention_days = 7  # Delete devices offline for 7+ days
        
        # Mark devices offline if not seen recently
        offline_count = self.device_repo.mark_offline_by_timeout(
            timeout_seconds=timeout,
            now=now
        )
        
        # Delete devices that have been offline too long
        deleted_count = self.device_repo.delete_offline_by_age(
            days=retention_days,
            now=now
        )
        
        return {
            "marked_offline": offline_count,
            "deleted_stale": deleted_count,
        }

    def cleanup_duplicate_devices(self) -> dict[str, int]:
        """Remove duplicate devices (same serial number, keep newest)."""
        count = self.device_repo.delete_duplicates()
        return {"duplicates_removed": count}
