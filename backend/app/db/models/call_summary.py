from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class CallSummary(Base, TimestampMixin):
    __tablename__ = "call_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    callback_required: Mapped[str] = mapped_column(
        String(50), default="unknown", nullable=False
    )
    urgency_level: Mapped[str] = mapped_column(
        String(50), default="unknown", nullable=False
    )
    sentiment: Mapped[str] = mapped_column(
        String(50), default="unknown", nullable=False
    )
    sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    call_session = relationship("CallSession", backref="summary", lazy="selectin")

    __table_args__ = (
        Index("ix_call_summaries_session", "call_session_id"),
        Index("ix_call_summaries_urgency", "urgency_level"),
        Index("ix_call_summaries_sentiment", "sentiment"),
        Index("ix_call_summaries_callback", "callback_required"),
    )
