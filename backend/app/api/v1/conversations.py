from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.conversation import (
    AnswerRequest,
    ConversationRead,
    LanguageSelectRequest,
)
from app.services.call_conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/current", response_model=SuccessResponse[ConversationRead | None])
def get_current_conversation(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[ConversationRead | None]:
    return SuccessResponse(data=ConversationService(db).get_current())


@router.get("/call/{call_session_id}", response_model=SuccessResponse[ConversationRead])
def get_call_conversation(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[ConversationRead]:
    return SuccessResponse(data=ConversationService(db).get_by_call(call_session_id))


@router.post("/call/{call_session_id}/language", response_model=SuccessResponse[ConversationRead])
async def select_language(
    call_session_id: int,
    request: LanguageSelectRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[ConversationRead]:
    conversation = await ConversationService(db).select_language(call_session_id, request.language)
    return SuccessResponse(message="Language selected", data=conversation)


@router.post("/call/{call_session_id}/answers", response_model=SuccessResponse[ConversationRead])
async def record_answer(
    call_session_id: int,
    request: AnswerRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[ConversationRead]:
    conversation = await ConversationService(db).record_answer(call_session_id, request.answer)
    return SuccessResponse(message="Answer recorded", data=conversation)
