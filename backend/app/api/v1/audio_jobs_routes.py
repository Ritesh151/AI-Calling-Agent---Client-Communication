from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.audio_processing_job_repository import AudioProcessingJobRepository
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/audio-jobs", tags=["Audio Processing Jobs"])


@router.get("/", response_model=SuccessResponse[list[dict]])
def list_jobs(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    repo = AudioProcessingJobRepository(db)
    if status:
        jobs = repo.get_by_status(status)
    else:
        jobs = repo.get_all(skip=skip, limit=limit)
    return SuccessResponse(data=[{
        "id": j.id,
        "recording_id": j.recording_id,
        "job_type": j.job_type,
        "status": j.status,
        "started_at": j.started_at,
        "completed_at": j.completed_at,
        "error_message": j.error_message,
        "retry_count": j.retry_count,
    } for j in jobs])


@router.get("/{recording_id}", response_model=SuccessResponse[list[dict]])
def get_recording_jobs(
    recording_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    repo = AudioProcessingJobRepository(db)
    jobs = repo.get_by_recording(recording_id)
    return SuccessResponse(data=[{
        "id": j.id,
        "recording_id": j.recording_id,
        "job_type": j.job_type,
        "status": j.status,
        "started_at": j.started_at,
        "completed_at": j.completed_at,
        "error_message": j.error_message,
        "retry_count": j.retry_count,
    } for j in jobs])
