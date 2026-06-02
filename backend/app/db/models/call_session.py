from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class CallSession(Base, TimestampMixin):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    caller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caller_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    call_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    recording_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcription: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    incoming_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    caller_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_call_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    device = relationship("Device", back_populates="call_sessions", lazy="selectin")
    conversation = relationship(
        "Conversation",
        back_populates="call_session",
        lazy="selectin",
        uselist=False,
        cascade="all, delete-orphan",
    )
