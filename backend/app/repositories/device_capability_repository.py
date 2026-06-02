from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.device_capability import DeviceCapability
from app.repositories.base import BaseRepository


class DeviceCapabilityRepository(BaseRepository[DeviceCapability]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, DeviceCapability)

    def get_by_device(self, device_id: int) -> DeviceCapability | None:
        return (
            self.db.query(DeviceCapability)
            .filter(DeviceCapability.device_id == device_id)
            .first()
        )

    def get_by_manufacturer(self, manufacturer: str) -> list[DeviceCapability]:
        return (
            self.db.query(DeviceCapability)
            .filter(DeviceCapability.manufacturer.ilike(manufacturer))
            .all()
        )

    def get_low_score(self, threshold: float = 50.0) -> list[DeviceCapability]:
        return (
            self.db.query(DeviceCapability)
            .filter(DeviceCapability.capability_score < threshold)
            .all()
        )
