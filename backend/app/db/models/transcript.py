from __future__ import annotations

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class Transcript(Base, TimestampMixin):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    recording_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    recording = relationship("Recording", back_populates="transcript", lazy="selectin")

    __table_args__ = (
        Index("ix_transcripts_recording", "recording_id"),
        Index("ix_transcripts_confidence", "confidence_score"),
    )
