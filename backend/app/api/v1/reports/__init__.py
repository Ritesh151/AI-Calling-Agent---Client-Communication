from fastapi import APIRouter

from app.api.v1.reports.report_routes import router as report_router

router = APIRouter(prefix="/reports", tags=["Reports"])
router.include_router(report_router)
