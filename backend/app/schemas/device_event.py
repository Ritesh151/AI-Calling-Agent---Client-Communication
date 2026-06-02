from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeviceEventCreate(BaseModel):
    device_id: int
    event_type: str
    event_name: str
    event_data: str | None = None


class DeviceEventRead(BaseModel):
    id: int
    device_id: int
    event_type: str
    event_name: str
    event_data: str | None
    event_time: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceEventFilter(BaseModel):
    device_id: int | None = None
    event_type: str | None = None
    limit: int = 100
