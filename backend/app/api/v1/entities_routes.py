from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.extracted_entity_repository import ExtractedEntityRepository
from app.schemas.common import SuccessResponse
from app.schemas.extracted_entity_schema import ExtractedEntityRead

router = APIRouter(prefix="/entities", tags=["Extracted Entities"])


@router.get("/", response_model=SuccessResponse[list[ExtractedEntityRead]])
def list_entities(
    entity_type: str | None = None,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[ExtractedEntityRead]]:
    repo = ExtractedEntityRepository(db)
    if entity_type:
        entities = repo.get_by_type(entity_type)
    else:
        entities = repo.get_all()
    return SuccessResponse(data=[ExtractedEntityRead.model_validate(e) for e in entities])


@router.get("/types", response_model=SuccessResponse[list[str]])
def list_entity_types(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[str]]:
    repo = ExtractedEntityRepository(db)
    types = repo.get_distinct_types()
    return SuccessResponse(data=types)


@router.get("/{call_session_id}", response_model=SuccessResponse[list[ExtractedEntityRead]])
def get_call_entities(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[ExtractedEntityRead]]:
    repo = ExtractedEntityRepository(db)
    entities = repo.get_by_session(call_session_id)
    return SuccessResponse(data=[ExtractedEntityRead.model_validate(e) for e in entities])
