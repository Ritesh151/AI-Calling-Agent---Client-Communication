from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.device_profile_model import DeviceProfile
from app.repositories.base import BaseRepository


class DeviceProfileRepository(BaseRepository[DeviceProfile]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, DeviceProfile)

    def get_by_manufacturer_model(self, manufacturer: str, model: str) -> DeviceProfile | None:
        return (
            self.db.query(DeviceProfile)
            .filter(
                DeviceProfile.manufacturer.ilike(manufacturer),
                DeviceProfile.model.ilike(f"%{model}%"),
            )
            .first()
        )

    def get_by_manufacturer(self, manufacturer: str) -> list[DeviceProfile]:
        return (
            self.db.query(DeviceProfile)
            .filter(DeviceProfile.manufacturer.ilike(manufacturer))
            .all()
        )

    def get_certified(self) -> list[DeviceProfile]:
        return (
            self.db.query(DeviceProfile)
            .filter(DeviceProfile.certification_level == "CERTIFIED")
            .all()
        )
