from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.setting_repository import SettingRepository
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate
from app.services.event_bus import event_bus
from app.services.event_bus.event_types import SettingsUpdatedEvent


class SettingService:
    def __init__(self, db: Session) -> None:
        self.setting_repo = SettingRepository(db)

    def create_setting(self, request: SettingCreate) -> SettingRead:
        setting = self.setting_repo.create(**request.model_dump())
        return SettingRead.model_validate(setting)

    def get_setting(self, setting_id: int) -> SettingRead:
        setting = self.setting_repo.get_by_id(setting_id)
        if not setting:
            raise NotFoundException("Setting not found")
        return SettingRead.model_validate(setting)

    def get_setting_by_key(self, key: str) -> SettingRead:
        setting = self.setting_repo.get_by_key(key)
        if not setting:
            raise NotFoundException(f"Setting '{key}' not found")
        return SettingRead.model_validate(setting)

    def get_all_settings(self, category: str | None = None) -> list[SettingRead]:
        if category:
            settings = self.setting_repo.get_by_category(category)
        else:
            settings = self.setting_repo.get_all()
        return [SettingRead.model_validate(s) for s in settings]

    def update_setting(self, setting_id: int, request: SettingUpdate) -> SettingRead:
        setting = self.setting_repo.get_by_id(setting_id)
        if not setting:
            raise NotFoundException("Setting not found")
        update_data = request.model_dump(exclude_unset=True)
        updated = self.setting_repo.update(setting_id, **update_data)
        return SettingRead.model_validate(updated)

    async def upsert_setting(self, key: str, request: SettingCreate | SettingUpdate) -> SettingRead:
        setting = self.setting_repo.upsert(
            key=key,
            value=request.value,
            description=getattr(request, "description", None),
            category=getattr(request, "category", None),
        )
        read = SettingRead.model_validate(setting)
        await event_bus.publish(
            SettingsUpdatedEvent(
                key=key,
                value=read.value,
                data={
                    "key": key,
                    "value": read.value,
                    "category": read.category,
                },
            )
        )
        return read

    def delete_setting(self, setting_id: int) -> None:
        if not self.setting_repo.delete(setting_id):
            raise NotFoundException("Setting not found")

    def get_all_as_dict(self) -> dict[str, str]:
        return self.setting_repo.get_all_as_dict()
