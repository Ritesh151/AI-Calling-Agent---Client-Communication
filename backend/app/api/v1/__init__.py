from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.devices import router as devices_router
from app.api.v1.calls import router as calls_router
from app.api.v1.settings import router as settings_router
from app.api.v1.logs import router as logs_router
from app.api.v1.system import router as system_router
from app.api.v1.events import router as events_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.adb_commands import router as adb_commands_router
from app.api.v1.recordings import router as recordings_router
from app.api.v1.transcripts import router as transcripts_router
from app.api.v1.greetings import router as greetings_router
from app.api.v1.greeting import router as greeting_router
from app.api.v1.archive import router as archive_router
from app.api.v1.audio_jobs_routes import router as audio_jobs_router
from app.api.v1.summaries_routes import router as summaries_router
from app.api.v1.entities_routes import router as entities_router
from app.api.v1.classifications_routes import router as classifications_router
from app.api.v1.ai_search import router as search_router
from app.api.v1.analytics_routes import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.insights import router as insights_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.projects import router as projects_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.call_export import router as call_export_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(devices_router)
api_router.include_router(calls_router)
api_router.include_router(settings_router)
api_router.include_router(logs_router)
api_router.include_router(system_router)
api_router.include_router(events_router)
api_router.include_router(metrics_router)
api_router.include_router(adb_commands_router)
api_router.include_router(recordings_router)
api_router.include_router(transcripts_router)
api_router.include_router(greetings_router)
api_router.include_router(greeting_router)
api_router.include_router(archive_router)
api_router.include_router(audio_jobs_router)
api_router.include_router(summaries_router)
api_router.include_router(entities_router)
api_router.include_router(classifications_router)
api_router.include_router(search_router)
api_router.include_router(analytics_router)
api_router.include_router(reports_router)
api_router.include_router(insights_router)
api_router.include_router(knowledge_router)
api_router.include_router(projects_router)
api_router.include_router(conversations_router)
api_router.include_router(call_export_router)

__all__ = ["api_router"]
