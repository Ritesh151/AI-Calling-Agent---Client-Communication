from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.transcript_schema import TranscriptRead
from app.services.transcription import TranscriptionService

router = APIRouter()


@router.get("/{recording_id}", response_model=SuccessResponse[TranscriptRead])
def get_transcript(
    recording_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[TranscriptRead]:
    service = TranscriptionService(db)
    transcript = service.get_transcript(recording_id)
    if not transcript:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Transcript not found")
    return SuccessResponse(data=TranscriptRead.model_validate(transcript))


@router.post("/{recording_id}/transcribe", response_model=SuccessResponse[TranscriptRead])
def transcribe_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[TranscriptRead]:
    service = TranscriptionService(db)
    transcript = service.transcribe_recording(recording_id)
    return SuccessResponse(message="Transcription completed", data=TranscriptRead.model_validate(transcript))
