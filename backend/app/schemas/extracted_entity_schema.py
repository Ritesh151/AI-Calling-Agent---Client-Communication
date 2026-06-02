from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedEntityCreate(BaseModel):
    call_session_id: int
    entity_type: str
    entity_value: str
    confidence_score: float = 0.0


class ExtractedEntityRead(BaseModel):
    id: int
    call_session_id: int
    entity_type: str
    entity_value: str
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class EntitySearchResult(BaseModel):
    entity_type: str
    entity_value: str
    call_session_id: int
    confidence_score: float
