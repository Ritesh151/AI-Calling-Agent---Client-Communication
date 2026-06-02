from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern=r"^(user|admin)$")


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$"
    )
    role: str | None = Field(default=None, pattern=r"^(user|admin)$")
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
