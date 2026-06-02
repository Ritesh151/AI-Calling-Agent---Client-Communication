from fastapi import APIRouter

from app.api.v1.knowledge.knowledge_routes import router as knowledge_router

router = APIRouter(prefix="/knowledge", tags=["Knowledge Center"])
router.include_router(knowledge_router)
