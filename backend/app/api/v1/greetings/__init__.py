from fastapi import APIRouter

from app.api.v1.greetings.greeting_routes import router as greetings_router

router = APIRouter(prefix="/greetings", tags=["Greetings"])
router.include_router(greetings_router)
