from __future__ import annotations

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    search_type: str = "hybrid"
    date_from: str | None = None
    date_to: str | None = None
    phone_number: str | None = None
    caller_name: str | None = None
    category: str | None = None
    sentiment: str | None = None
    urgency: str | None = None
    callback_required: str | None = None
    device_id: int | None = None
    min_duration: int | None = None
    max_duration: int | None = None
    limit: int = 20
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"


class SearchResult(BaseModel):
    id: int
    call_session_id: int
    transcript_text: str | None
    summary: str | None
    short_summary: str | None
    category: str | None
    sentiment: str | None
    urgency: str | None
    callback_required: str | None
    caller_number: str | None
    caller_name: str | None
    duration: float | None
    created_at: str | None
    score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
    search_type: str
    took_ms: float
