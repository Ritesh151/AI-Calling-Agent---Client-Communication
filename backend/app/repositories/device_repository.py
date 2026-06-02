from __future__ import annotations

from sqlalchemy import and_, func
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

    def mark_offline_by_timeout(
        self, timeout_seconds: int = 10, now = None
    ) -> int:
        """Mark devices offline if not seen in timeout_seconds."""
        from datetime import UTC, timedelta, datetime as dt
        
        if now is None:
            now = dt.now(UTC)
        
        timeout_time = now - timedelta(seconds=timeout_seconds)
        
        # Update devices that are marked connected but haven't been seen
        result = self.db.query(Device).filter(
            and_(
                Device.is_connected.is_(True),
                Device.last_seen < timeout_time,
            )
        ).update({Device.is_connected: False, Device.status: "disconnected"})
        
        self.db.commit()
        return result

    def delete_offline_by_age(
        self, days: int = 7, now = None
    ) -> int:
        """Delete devices that have been offline for days."""
        from datetime import UTC, timedelta, datetime as dt
        
        if now is None:
            now = dt.now(UTC)
        
        cutoff_time = now - timedelta(days=days)
        
        # Delete devices that are disconnected and haven't been seen in days
        result = self.db.query(Device).filter(
            and_(
                Device.is_connected.is_(False),
                Device.last_seen < cutoff_time,
            )
        ).delete()
        
        self.db.commit()
        return result

    def delete_duplicates(self) -> int:
        """Delete duplicate devices (same serial), keeping the newest."""
        from sqlalchemy import text
        
        # Find duplicates
        duplicates = self.db.query(
            Device.serial_number,
            func.max(Device.id).label("max_id")
        ).filter(
            Device.serial_number.isnot(None)
        ).group_by(Device.serial_number).having(
            func.count(Device.id) > 1
        ).all()
        
        deleted = 0
        for serial_number, max_id in duplicates:
            result = self.db.query(Device).filter(
                and_(
                    Device.serial_number == serial_number,
                    Device.id != max_id
                )
            ).delete()
            deleted += result
        
        self.db.commit()
        return deleted
