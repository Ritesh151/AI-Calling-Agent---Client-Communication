from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GreetingTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    language: str = "en-US"
    template_text: str = Field(..., min_length=1)
    is_default: bool = False
    voice: str | None = None


class GreetingTemplateUpdate(BaseModel):
    name: str | None = None
    language: str | None = None
    template_text: str | None = None
    is_default: bool | None = None
    voice: str | None = None


class GreetingTemplateRead(BaseModel):
    id: int
    name: str
    language: str
    template_text: str
    is_default: bool
    voice: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
