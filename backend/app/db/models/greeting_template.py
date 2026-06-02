from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.db.models.base import TimestampMixin


class GreetingTemplate(Base, TimestampMixin):
    __tablename__ = "greeting_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en-US", nullable=False)
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voice: Mapped[str | None] = mapped_column(String(100), nullable=True)
