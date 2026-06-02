from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.call_session import CallSessionCreate, CallSessionRead, CallSessionUpdate
from app.schemas.common import SuccessResponse
from app.services.call_session_service import CallSessionService

router = APIRouter(prefix="/calls", tags=["Call Sessions"])


@router.get("/", response_model=SuccessResponse[list[CallSessionRead]])
def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallSessionRead]]:
    service = CallSessionService(db)
    sessions = service.get_all_sessions(skip=skip, limit=limit)
    return SuccessResponse(data=sessions)


@router.get("/active", response_model=SuccessResponse[list[CallSessionRead]])
def list_active_sessions(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallSessionRead]]:
    service = CallSessionService(db)
    sessions = service.get_active_sessions()
    return SuccessResponse(data=sessions)


@router.get("/device/{device_id}", response_model=SuccessResponse[list[CallSessionRead]])
def get_device_sessions(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallSessionRead]]:
    service = CallSessionService(db)
    sessions = service.get_device_sessions(device_id)
    return SuccessResponse(data=sessions)


@router.get("/{session_id}", response_model=SuccessResponse[CallSessionRead])
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[CallSessionRead]:
    service = CallSessionService(db)
    session = service.get_session(session_id)
    return SuccessResponse(data=session)


@router.post("/", response_model=SuccessResponse[CallSessionRead])
def create_session(
    request: CallSessionCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[CallSessionRead]:
    service = CallSessionService(db)
    session = service.create_session(request)
    return SuccessResponse(message="Call session created", data=session)


@router.put("/{session_id}", response_model=SuccessResponse[CallSessionRead])
def update_session(
    session_id: int,
    request: CallSessionUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[CallSessionRead]:
    service = CallSessionService(db)
    session = service.update_session(session_id, request)
    return SuccessResponse(message="Call session updated", data=session)
