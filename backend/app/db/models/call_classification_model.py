from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class CallClassification(Base, TimestampMixin):
    __tablename__ = "call_classifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    call_session = relationship("CallSession", backref="classifications", lazy="selectin")

    __table_args__ = (
        Index("ix_call_classifications_session", "call_session_id"),
        Index("ix_call_classifications_category", "category"),
    )
