from fastapi import APIRouter

from app.api.v1.ai_search.search_routes import router as search_router

router = APIRouter(prefix="/search", tags=["AI Search"])
router.include_router(search_router)
