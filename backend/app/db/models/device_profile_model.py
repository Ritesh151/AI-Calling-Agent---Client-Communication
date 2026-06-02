from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.db.models.base import TimestampMixin


class DeviceProfile(Base, TimestampMixin):
    __tablename__ = "device_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    android_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supported_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_strategy: Mapped[str] = mapped_column(String(100), default="generic", nullable=False)
    certification_level: Mapped[str] = mapped_column(String(50), default="UNSUPPORTED", nullable=False)

    __table_args__ = (
        Index("ix_device_profiles_manufacturer_model", "manufacturer", "model"),
    )
