from fastapi import APIRouter

from app.api.v1.insights.insight_routes import router as insight_router

router = APIRouter(prefix="/insights", tags=["AI Insights"])
router.include_router(insight_router)
