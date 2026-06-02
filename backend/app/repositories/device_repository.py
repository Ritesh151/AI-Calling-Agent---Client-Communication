from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Device)

    def get_by_serial(self, serial_number: str) -> Device | None:
        return (
            self.db.query(Device)
            .filter(Device.serial_number == serial_number)
            .first()
        )

    def get_by_android_id(self, android_id: str) -> Device | None:
        return (
            self.db.query(Device).filter(Device.android_id == android_id).first()
        )

    def get_connected_devices(self) -> list[Device]:
        return (
            self.db.query(Device)
            .filter(Device.is_connected.is_(True))
            .all()
        )

    def get_user_devices(self, user_id: int) -> list[Device]:
        return (
            self.db.query(Device)
            .filter(Device.user_id == user_id)
            .all()
        )

    def update_heartbeat(self, device_id: int) -> Device | None:
        from datetime import UTC, datetime

        return self.update(device_id, last_seen=datetime.now(UTC))
