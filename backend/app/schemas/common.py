from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: T | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str = "An error occurred"
    error_code: str = "INTERNAL_ERROR"
    details: dict[str, Any] | None = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(SuccessResponse, Generic[T]):
    page: int
    page_size: int
    total: int
    total_pages: int
    data: list[T]
