from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AIProcessingJobCreate(BaseModel):
    call_session_id: int
    job_type: str


class AIProcessingJobRead(BaseModel):
    id: int
    call_session_id: int
    job_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}
