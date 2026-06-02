from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.setting import Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Setting)

    def get_by_key(self, key: str) -> Setting | None:
        return self.db.query(Setting).filter(Setting.key == key).first()

    def get_by_category(self, category: str) -> list[Setting]:
        return (
            self.db.query(Setting)
            .filter(Setting.category == category)
            .all()
        )

    def upsert(self, key: str, value: str, description: str | None = None, category: str | None = None) -> Setting:
        existing = self.get_by_key(key)
        if existing:
            return self.update(existing.id, value=value, description=description, category=category)
        return self.create(key=key, value=value, description=description, category=category)

    def get_value(self, key: str, default: str = "") -> str:
        setting = self.get_by_key(key)
        if setting:
            return setting.value
        return default

    def get_all_as_dict(self) -> dict[str, str]:
        settings = self.get_all()
        return {s.key: s.value for s in settings}
