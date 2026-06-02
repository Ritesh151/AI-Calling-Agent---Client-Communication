from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class EmbeddingRecord(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    embedding_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    vector_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    call_session = relationship("CallSession", backref="embeddings", lazy="selectin")

    __table_args__ = (
        Index("ix_embeddings_session", "call_session_id"),
        Index("ix_embeddings_vector", "vector_id", unique=True),
        Index("ix_embeddings_provider_model", "embedding_provider", "embedding_model"),
    )
