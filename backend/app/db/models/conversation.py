from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.db.models.base import TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="language_selection", nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_slug: Mapped[str | None] = mapped_column(String(150), nullable=True)
    client_database: Mapped[str | None] = mapped_column(String(180), nullable=True)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    call_session = relationship("CallSession", back_populates="conversation", lazy="selectin")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )


class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    call_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)
    message_type: Mapped[str] = mapped_column(String(30), default="message", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    question_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_key: Mapped[str | None] = mapped_column(String(100), nullable=True)

    conversation = relationship("Conversation", back_populates="messages", lazy="selectin")
