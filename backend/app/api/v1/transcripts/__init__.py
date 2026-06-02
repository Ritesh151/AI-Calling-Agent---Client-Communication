from fastapi import APIRouter

from app.api.v1.transcripts.transcript_routes import router as transcripts_router

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])
router.include_router(transcripts_router)
