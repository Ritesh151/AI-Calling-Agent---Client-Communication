from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class RecoveryLog(Base, TimestampMixin):
    __tablename__ = "recovery_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recovery_action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    device = relationship("Device", backref="recovery_logs", lazy="selectin")

    __table_args__ = (
        Index("ix_recovery_logs_device", "device_id"),
        Index("ix_recovery_logs_status", "status"),
    )
