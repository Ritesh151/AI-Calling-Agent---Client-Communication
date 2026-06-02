from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecordingCreate(BaseModel):
    call_session_id: int
    device_id: int | None = None
    filename: str
    file_path: str
    storage_type: str = "local"
    file_size: int | None = None
    duration_seconds: float | None = None
    audio_format: str = "wav"


class RecordingUpdate(BaseModel):
    recording_status: str | None = None
    file_size: int | None = None
    duration_seconds: float | None = None
    checksum: str | None = None


class RecordingRead(BaseModel):
    id: int
    call_session_id: int
    device_id: int | None
    filename: str
    file_path: str
    storage_type: str
    file_size: int | None
    duration_seconds: float | None
    audio_format: str
    recording_status: str
    checksum: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordingFilter(BaseModel):
    call_session_id: int | None = None
    device_id: int | None = None
    recording_status: str | None = None
