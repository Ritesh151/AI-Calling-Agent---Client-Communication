from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class ExtractedEntity(Base, TimestampMixin):
    __tablename__ = "extracted_entities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    call_session = relationship("CallSession", backref="entities", lazy="selectin")

    __table_args__ = (
        Index("ix_extracted_entities_session", "call_session_id"),
        Index("ix_extracted_entities_type", "entity_type"),
        Index("ix_extracted_entities_value", "entity_value", mysql_prefix="FULLTEXT"),
    )
