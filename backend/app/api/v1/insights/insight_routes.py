from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.services.insights import InsightService

router = APIRouter()


@router.get("/", response_model=SuccessResponse[list[dict]])
def get_insights(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    service = InsightService(db)
    insights = service.generate_insights()
    return SuccessResponse(data=insights)
