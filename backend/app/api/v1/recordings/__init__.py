from fastapi import APIRouter

from app.api.v1.recordings.recording_routes import router as recordings_router

router = APIRouter(prefix="/recordings", tags=["Recordings"])
router.include_router(recordings_router)
