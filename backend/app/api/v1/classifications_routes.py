from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.call_classification_repository import CallClassificationRepository
from app.schemas.call_classification_schema import CallClassificationRead
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/classifications", tags=["Call Classifications"])


@router.get("/", response_model=SuccessResponse[list[CallClassificationRead]])
def list_classifications(
    category: str | None = None,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallClassificationRead]]:
    repo = CallClassificationRepository(db)
    if category:
        classifications = repo.get_by_category(category)
    else:
        classifications = repo.get_all()
    return SuccessResponse(data=[CallClassificationRead.model_validate(c) for c in classifications])


@router.get("/categories", response_model=SuccessResponse[list[str]])
def list_categories(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[str]]:
    repo = CallClassificationRepository(db)
    cats = repo.get_distinct_categories()
    return SuccessResponse(data=cats)


@router.get("/{call_session_id}", response_model=SuccessResponse[list[CallClassificationRead]])
def get_call_classifications(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[CallClassificationRead]]:
    repo = CallClassificationRepository(db)
    classifications = repo.get_by_session(call_session_id)
    return SuccessResponse(data=[CallClassificationRead.model_validate(c) for c in classifications])
