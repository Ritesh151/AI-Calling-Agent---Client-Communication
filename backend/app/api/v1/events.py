from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.base import BaseRepository
from app.db.models.device_event import DeviceEvent
from app.schemas.common import SuccessResponse
from app.schemas.device_event import DeviceEventRead

router = APIRouter(prefix="/events", tags=["Device Events"])


@router.get("/", response_model=SuccessResponse[list[DeviceEventRead]])
def list_events(
    device_id: int | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[DeviceEventRead]]:
    repo = BaseRepository(db, DeviceEvent)
    query = db.query(DeviceEvent)
    if device_id:
        query = query.filter(DeviceEvent.device_id == device_id)
    if event_type:
        query = query.filter(DeviceEvent.event_type == event_type)
    events = query.order_by(DeviceEvent.event_time.desc()).limit(limit).all()
    return SuccessResponse(
        data=[DeviceEventRead.model_validate(e) for e in events]
    )
