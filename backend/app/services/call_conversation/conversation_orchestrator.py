from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.services.call_conversation.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Runs greeting + requirement capture when a call becomes active."""

    async def on_call_active(
        self,
        *,
        call_session_id: int,
        device_id: int,
        serial: str,
        caller_number: str,
        auto_answered: bool = False,
    ) -> dict:
        db = SessionLocal()
        try:
            service = ConversationService(db)
            conversation = await service.ensure_for_call(call_session_id)
            logger.info("Conversation started for call_session=%s", call_session_id)
            return {
                "conversation_id": conversation.id,
                "questions_count": conversation.total_questions,
                "auto_answered": auto_answered,
            }
        except Exception as exc:
            logger.error("Conversation orchestrator failed: %s", exc)
            db.rollback()
            return {"error": str(exc)}
        finally:
            db.close()
