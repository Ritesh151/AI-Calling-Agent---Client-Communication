from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SystemLogRead(BaseModel):
    id: int
    level: str
    module: str
    message: str
    metadata_json: str | None
    logged_at: datetime

    model_config = {"from_attributes": True}
