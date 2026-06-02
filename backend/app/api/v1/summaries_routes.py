from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.call_summary_repository import CallSummaryRepository
from app.schemas.call_summary import CallSummaryRead
from app.schemas.common import SuccessResponse
from app.services.ai_analysis.analysis_orchestrator import AnalysisOrchestrator

router = APIRouter(prefix="/summaries", tags=["Call Summaries"])


@router.get("/", response_model=SuccessResponse[list[CallSummaryRead]])
def list_summaries(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallSummaryRead]]:
    repo = CallSummaryRepository(db)
    summaries = repo.get_all()
    return SuccessResponse(data=[CallSummaryRead.model_validate(s) for s in summaries])


@router.get("/{call_session_id}", response_model=SuccessResponse[CallSummaryRead])
def get_summary(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[CallSummaryRead]:
    repo = CallSummaryRepository(db)
    summary = repo.get_by_session(call_session_id)
    if not summary:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Summary not found")
    return SuccessResponse(data=CallSummaryRead.model_validate(summary))


@router.post("/{call_session_id}/generate", response_model=SuccessResponse[CallSummaryRead])
def generate_summary(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[CallSummaryRead]:
    from app.db.models.transcript import Transcript
    transcript = db.query(Transcript).filter(Transcript.recording_id == call_session_id).first()
    if not transcript or not transcript.transcript_text:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Transcript not found for this call")

    orchestrator = AnalysisOrchestrator(db)
    orchestrator.analyze_call(call_session_id, transcript.transcript_text)

    repo = CallSummaryRepository(db)
    summary = repo.get_by_session(call_session_id)
    return SuccessResponse(message="Summary generated", data=CallSummaryRead.model_validate(summary))
