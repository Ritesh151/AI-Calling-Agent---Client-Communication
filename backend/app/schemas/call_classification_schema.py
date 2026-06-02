from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CallClassificationCreate(BaseModel):
    call_session_id: int
    category: str
    subcategory: str | None = None
    confidence_score: float = 0.0


class CallClassificationRead(BaseModel):
    id: int
    call_session_id: int
    category: str
    subcategory: str | None
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassificationResult(BaseModel):
    primary_category: str
    primary_confidence: float
    secondary_categories: list[dict] = []
