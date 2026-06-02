"""
Greeting API endpoints - Fixed greeting flow with language selection
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.common import SuccessResponse
from app.services.greeting_engine import GreetingEngine
from app.core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/greetings", tags=["greeting"])


@router.post("/start/{call_session_id}")
async def start_greeting(
    call_session_id: int,
    device_id: int,
    serial: str,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Start the initial greeting flow
    
    Plays multi-language greeting asking for language selection (1/2/3)
    """
    try:
        engine = GreetingEngine(db)
        result = await engine.play_initial_greeting(
            call_session_id=call_session_id,
            device_id=device_id,
            serial=serial
        )
        return SuccessResponse(
            data=result,
            message="Greeting started"
        )
    except NotFoundException as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error("Error starting greeting: %s", e)
        raise ValidationException(str(e))


@router.post("/select-language/{call_session_id}")
async def select_language(
    call_session_id: int,
    language_input: str,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Process language selection (1/2/3 or spoken language)
    
    Returns confirmation greeting in selected language
    """
    try:
        if not language_input or not language_input.strip():
            raise ValidationException("Language input is required")
        
        engine = GreetingEngine(db)
        result = await engine.process_language_selection(
            call_session_id=call_session_id,
            language_input=language_input
        )
        
        if result["status"] != "language_confirmed":
            raise ValidationException(result.get("reason", "Invalid language selection"))
        
        return SuccessResponse(
            data=result,
            message="Language selected and confirmed"
        )
    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error("Error selecting language: %s", e)
        raise ValidationException(str(e))


@router.post("/complete/{call_session_id}")
async def complete_greeting(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Mark greeting as completed and ready for question engine
    """
    try:
        engine = GreetingEngine(db)
        result = await engine.complete_greeting(call_session_id)
        return SuccessResponse(
            data=result,
            message="Greeting completed. Ready for question engine."
        )
    except NotFoundException as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error("Error completing greeting: %s", e)
        raise ValidationException(str(e))


@router.get("/status/{call_session_id}")
def get_greeting_status(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Get current greeting status for a call
    """
    try:
        engine = GreetingEngine(db)
        status = engine.get_greeting_status(call_session_id)
        return SuccessResponse(data=status)
    except NotFoundException as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error("Error getting greeting status: %s", e)
        raise ValidationException(str(e))
