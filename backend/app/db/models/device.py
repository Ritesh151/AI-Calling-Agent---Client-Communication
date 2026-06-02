from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    android_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    android_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="disconnected", nullable=False
    )
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usb_debugging_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    adb_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_command_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    device_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    charging: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    screen_state: Mapped[str | None] = mapped_column(String(20), nullable=True)

    owner = relationship("User", back_populates="devices", lazy="selectin")
    call_sessions = relationship("CallSession", back_populates="device", lazy="selectin")
    device_events = relationship("DeviceEvent", back_populates="device", lazy="selectin")
    device_metrics = relationship("DeviceMetric", back_populates="device", lazy="selectin")
    adb_commands = relationship("ADBCommand", back_populates="device", lazy="selectin")
