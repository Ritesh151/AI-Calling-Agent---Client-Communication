from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ADBCommandCreate(BaseModel):
    device_id: int
    command: str
    command_type: str | None = None


class ADBCommandRead(BaseModel):
    id: int
    device_id: int
    command: str
    command_type: str | None
    status: str
    execution_time: float | None
    response: str | None
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
