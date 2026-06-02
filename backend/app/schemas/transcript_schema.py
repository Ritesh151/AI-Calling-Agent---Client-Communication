from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TranscriptCreate(BaseModel):
    recording_id: int
    language: str | None = None
    transcript_text: str | None = None
    raw_transcript: str | None = None
    confidence_score: float | None = None
    processing_time: float | None = None


class TranscriptRead(BaseModel):
    id: int
    recording_id: int
    language: str | None
    transcript_text: str | None
    word_count: int | None
    confidence_score: float | None
    processing_time: float | None
    raw_transcript: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
