from fastapi import APIRouter

from app.api.v1.archive.archive_routes import router as archive_router

router = APIRouter(prefix="/archive", tags=["Archive"])
router.include_router(archive_router)
