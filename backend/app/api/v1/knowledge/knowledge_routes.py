from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.services.knowledge_engine import KnowledgeService

router = APIRouter()


@router.get("/calls/{call_session_id}", response_model=SuccessResponse[dict])
def get_call_knowledge(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = KnowledgeService(db)
    knowledge = service.get_call_knowledge(call_session_id)
    return SuccessResponse(data=knowledge)


@router.get("/search", response_model=SuccessResponse[list[dict]])
def search_knowledge(
    q: str = Query(..., min_length=1),
    limit: int = Query(20),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    service = KnowledgeService(db)
    results = service.search_knowledge(q, limit=limit)
    return SuccessResponse(data=results)


@router.get("/topics", response_model=SuccessResponse[list[dict]])
def get_topics(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    service = KnowledgeService(db)
    topics = service.get_topic_discovery()
    return SuccessResponse(data=topics)


@router.get("/entity-types", response_model=SuccessResponse[list[dict]])
def get_entity_types(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    service = KnowledgeService(db)
    types = service.get_entity_types()
    return SuccessResponse(data=types)
