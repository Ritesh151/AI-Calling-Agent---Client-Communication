from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.recording import RecordingCreate, RecordingRead, RecordingUpdate
from app.services.recording_engine import RecordingService

router = APIRouter()


@router.get("/", response_model=SuccessResponse[list[RecordingRead]])
def list_recordings(
    call_session_id: int | None = Query(None),
    device_id: int | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[RecordingRead]]:
    service = RecordingService(db)
    if call_session_id:
        recordings = service.get_call_recordings(call_session_id)
    else:
        recordings = service.repo.get_all(skip=skip, limit=limit)
    return SuccessResponse(data=[RecordingRead.model_validate(r) for r in recordings])


@router.get("/{recording_id}", response_model=SuccessResponse[RecordingRead])
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[RecordingRead]:
    service = RecordingService(db)
    recording = service.get_recording(recording_id)
    if not recording:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Recording not found")
    return SuccessResponse(data=RecordingRead.model_validate(recording))


@router.post("/", response_model=SuccessResponse[RecordingRead])
def create_recording(
    request: RecordingCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[RecordingRead]:
    service = RecordingService(db)
    recording = service.repo.create(**request.model_dump())
    return SuccessResponse(message="Recording created", data=RecordingRead.model_validate(recording))


@router.put("/{recording_id}", response_model=SuccessResponse[RecordingRead])
def update_recording(
    recording_id: int,
    request: RecordingUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[RecordingRead]:
    service = RecordingService(db)
    recording = service.repo.update(recording_id, **request.model_dump(exclude_unset=True))
    if not recording:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Recording not found")
    return SuccessResponse(message="Recording updated", data=RecordingRead.model_validate(recording))


@router.delete("/{recording_id}", response_model=SuccessResponse[dict])
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = RecordingService(db)
    recording = service.get_recording(recording_id)
    if not recording:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Recording not found")
    import os
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    service.repo.delete(recording_id)
    return SuccessResponse(message="Recording deleted", data={})
