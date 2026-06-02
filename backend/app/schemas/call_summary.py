from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CallSummaryCreate(BaseModel):
    call_session_id: int
    summary: str | None = None
    short_summary: str | None = None
    action_items: str | None = None
    callback_required: str = "unknown"
    urgency_level: str = "unknown"
    sentiment: str = "unknown"
    sentiment_confidence: float | None = None
    sentiment_reasoning: str | None = None


class CallSummaryRead(BaseModel):
    id: int
    call_session_id: int
    summary: str | None
    short_summary: str | None
    action_items: str | None
    callback_required: str
    urgency_level: str
    sentiment: str
    sentiment_confidence: float | None
    sentiment_reasoning: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallSummarySearchResult(BaseModel):
    id: int
    call_session_id: int
    short_summary: str | None
    urgency_level: str
    sentiment: str
    callback_required: str
