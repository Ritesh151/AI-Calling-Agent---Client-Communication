from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, require_role
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate
from app.services.setting_service import SettingService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=SuccessResponse[list[SettingRead]])
def list_settings(
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[SettingRead]]:
    service = SettingService(db)
    settings = service.get_all_settings(category=category)
    return SuccessResponse(data=settings)


@router.get("/{setting_id}", response_model=SuccessResponse[SettingRead])
def get_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[SettingRead]:
    service = SettingService(db)
    setting = service.get_setting(setting_id)
    return SuccessResponse(data=setting)


@router.get("/key/{key}", response_model=SuccessResponse[SettingRead])
def get_setting_by_key(
    key: str,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[SettingRead]:
    service = SettingService(db)
    setting = service.get_setting_by_key(key)
    return SuccessResponse(data=setting)


@router.post("/", response_model=SuccessResponse[SettingRead])
def create_setting(
    request: SettingCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[SettingRead]:
    service = SettingService(db)
    setting = service.create_setting(request)
    return SuccessResponse(message="Setting created", data=setting)


@router.put("/{setting_id}", response_model=SuccessResponse[SettingRead])
def update_setting(
    setting_id: int,
    request: SettingUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[SettingRead]:
    service = SettingService(db)
    setting = service.update_setting(setting_id, request)
    return SuccessResponse(message="Setting updated", data=setting)


@router.put("/key/{key}", response_model=SuccessResponse[SettingRead])
async def upsert_setting(
    key: str,
    request: SettingUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[SettingRead]:
    service = SettingService(db)
    setting = await service.upsert_setting(key, request)
    return SuccessResponse(message="Setting saved", data=setting)


@router.delete("/{setting_id}", response_model=SuccessResponse[None])
def delete_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[None]:
    service = SettingService(db)
    service.delete_setting(setting_id)
    return SuccessResponse(message="Setting deleted")
