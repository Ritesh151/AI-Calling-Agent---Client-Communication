from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LanguageSelectRequest(BaseModel):
    language: str = Field(pattern=r"^(english|hindi|gujarati|en|hi|gu)$")


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


class ConversationMessageRead(BaseModel):
    id: int
    conversation_id: int
    call_session_id: int
    speaker: str
    message_type: str
    content: str
    language: str | None
    question_index: int | None
    question_key: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationRead(BaseModel):
    id: int
    call_session_id: int
    language: str | None
    service_type: str | None
    client_slug: str | None
    client_database: str | None
    status: str
    current_question_index: int
    total_questions: int
    completion_percentage: int
    profile_json: str | None
    requirements_json: str | None
    transcript: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageRead] = []

    model_config = {"from_attributes": True}
