from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class DeviceCapability(Base, TimestampMixin):
    __tablename__ = "device_capabilities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    android_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    supports_auto_answer: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_call_detection: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_audio_capture: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_speaker_recording: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_mic_recording: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_tts_playback: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_background_execution: Mapped[bool] = mapped_column(Boolean, default=False)

    capability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    certification_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    device = relationship("Device", backref="capabilities", lazy="selectin")

    __table_args__ = (
        Index("ix_device_capabilities_device", "device_id"),
        Index("ix_device_capabilities_manufacturer", "manufacturer"),
    )
