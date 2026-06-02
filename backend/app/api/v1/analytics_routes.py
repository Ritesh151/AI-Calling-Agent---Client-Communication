from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.analytics_schema import AnalyticsDashboard
from app.schemas.common import SuccessResponse
from app.services.analytics_engine import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=SuccessResponse[AnalyticsDashboard])
def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[AnalyticsDashboard]:
    service = AnalyticsService(db)
    dash = service.get_dashboard(days=days)
    return SuccessResponse(data=AnalyticsDashboard(**dash))
