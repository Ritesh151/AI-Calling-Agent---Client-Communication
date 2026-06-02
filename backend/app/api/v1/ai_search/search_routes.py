from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.search_schema import SearchQuery, SearchResponse, SearchResult
from app.services.semantic_search import SearchService

router = APIRouter()


@router.post("/", response_model=SuccessResponse[SearchResponse])
def search(
    query: SearchQuery,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[SearchResponse]:
    service = SearchService(db)
    filters = {
        k: v for k, v in {
            "category": query.category,
            "sentiment": query.sentiment,
            "urgency": query.urgency,
            "callback_required": query.callback_required,
            "phone_number": query.phone_number,
            "caller_name": query.caller_name,
        }.items() if v
    }
    result = service.search(
        query=query.query,
        search_type=query.search_type,
        limit=query.limit,
        filters=filters,
    )
    return SuccessResponse(data=SearchResponse(**result))


@router.get("/", response_model=SuccessResponse[SearchResponse])
def search_get(
    q: str = Query(..., min_length=1),
    search_type: str = Query("hybrid"),
    limit: int = Query(20),
    category: str | None = Query(None),
    sentiment: str | None = Query(None),
    urgency: str | None = Query(None),
    callback_required: str | None = Query(None),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[SearchResponse]:
    service = SearchService(db)
    filters = {
        k: v for k, v in {
            "category": category,
            "sentiment": sentiment,
            "urgency": urgency,
            "callback_required": callback_required,
        }.items() if v
    }
    result = service.search(query=q, search_type=search_type, limit=limit, filters=filters)
    return SuccessResponse(data=SearchResponse(**result))
