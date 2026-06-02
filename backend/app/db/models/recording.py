from __future__ import annotations

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class Recording(Base, TimestampMixin):
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_format: Mapped[str] = mapped_column(String(20), default="wav", nullable=False)
    recording_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    call_session = relationship("CallSession", backref="recordings", lazy="selectin")
    transcript = relationship("Transcript", back_populates="recording", uselist=False, lazy="selectin")

    __table_args__ = (
        Index("ix_recordings_call_session", "call_session_id"),
        Index("ix_recordings_device_status", "device_id", "recording_status"),
    )
