from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CallSessionCreate(BaseModel):
    device_id: int
    caller_name: str | None = None
    caller_number: str | None = None
    call_status: str = Field(default="pending", pattern=r"^(pending|idle|ringing|answering|active|ended|missed|failed)$")
    language: str | None = None


class CallSessionUpdate(BaseModel):
    caller_name: str | None = None
    caller_number: str | None = None
    call_status: str | None = Field(
        default=None, pattern=r"^(pending|idle|ringing|answering|active|ended|missed|failed)$"
    )
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: float | None = None
    recording_path: str | None = None
    transcription: str | None = None
    incoming_detected_at: datetime | None = None
    answered_at: datetime | None = None
    language: str | None = None
    caller_type: str | None = None
    raw_call_data: str | None = None


class CallSessionRead(BaseModel):
    id: int
    device_id: int
    caller_name: str | None
    caller_number: str | None
    call_status: str
    start_time: datetime | None
    end_time: datetime | None
    duration: float | None
    recording_path: str | None
    transcription: str | None
    incoming_detected_at: datetime | None
    answered_at: datetime | None
    language: str | None
    caller_type: str | None
    raw_call_data: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
