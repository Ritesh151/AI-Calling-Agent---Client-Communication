from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SettingCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    value: str = Field(..., min_length=0)
    description: str | None = None
    category: str | None = Field(
        default=None,
        pattern=r"^(general|greeting|recording|transcription|system|device)$",
    )


class SettingUpdate(BaseModel):
    value: str = Field(..., min_length=0)
    description: str | None = None
    category: str | None = Field(
        default=None,
        pattern=r"^(general|greeting|recording|transcription|system|device)$",
    )


class SettingRead(BaseModel):
    id: int
    key: str
    value: str
    description: str | None
    category: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}
