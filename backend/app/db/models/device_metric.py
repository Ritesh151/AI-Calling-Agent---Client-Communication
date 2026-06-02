from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeviceMetric(Base):
    __tablename__ = "device_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    charging: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    screen_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    usb_connected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    signal_strength: Mapped[int | None] = mapped_column(Integer, nullable=True)
    network_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cpu_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    device = relationship("Device", back_populates="device_metrics", lazy="selectin")

    __table_args__ = (
        Index("ix_device_metrics_device_captured", "device_id", "captured_at"),
    )
