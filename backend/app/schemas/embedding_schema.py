from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EmbeddingCreate(BaseModel):
    call_session_id: int
    embedding_provider: str
    embedding_model: str
    vector_id: str
    chunk_text: str | None = None
    chunk_index: int | None = None


class EmbeddingRead(BaseModel):
    id: int
    call_session_id: int
    embedding_provider: str
    embedding_model: str
    vector_id: str
    chunk_text: str | None
    chunk_index: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmbeddingSearchQuery(BaseModel):
    query: str
    limit: int = 10
    filters: dict | None = None


class EmbeddingSearchResult(BaseModel):
    call_session_id: int
    chunk_text: str
    score: float
    metadata: dict = {}
