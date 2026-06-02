from __future__ import annotations

import platform
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, require_role
from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.services.call_session_service import CallSessionService
from app.services.device_service import DeviceService
from app.services.log_service import LogService
from app.services.user_service import UserService

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
def health_check() -> dict:
    return {
        "success": True,
        "message": "System is healthy",
        "data": {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": settings.PROJECT_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    }


@router.get("/stats", response_model=SuccessResponse[dict])
async def system_stats(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    from app.services.device_sync import device_sync_service

    device_service = DeviceService(db)
    call_service = CallSessionService(db)
    user_service = UserService(db)
    log_service = LogService(db)
    sync_result = await device_sync_service.sync(db)

    return SuccessResponse(
        data={
            "total_devices": sync_result.connected_count,
            "connected_devices": sync_result.connected_count,
            "total_calls": call_service.get_session_count(),
            "active_calls": call_service.get_active_session_count(),
            "total_users": user_service.get_user_count(),
            "total_logs": log_service.get_log_count(),
            "server_time": datetime.now(UTC).isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        }
    )


@router.get("/diagnostics", response_model=SuccessResponse[dict])
async def system_diagnostics(
    request: Request,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    from sqlalchemy import text

    from app.core.config import settings
    from app.services.adb_watcher import adb_engine
    from app.services.call_detector.auto_answer import AutoAnswerService
    from app.services.device_sync import device_sync_service
    from app.services.event_bus import event_bus
    from app.services.websocket import ws_manager
    from app.workers.registry import get_worker_status

    db_status = "healthy"
    db_message = "OK"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "unhealthy"
        db_message = str(exc)

    redis_status = "healthy"
    redis_message = "OK"
    try:
        import redis

        r = redis.Redis.from_url(str(settings.REDIS_URL))
        r.ping()
    except Exception as exc:
        redis_status = "unhealthy"
        redis_message = str(exc)

    adb_health = await adb_engine.health_check()
    device_sync = await device_sync_service.sync(db)

    answer_service = AutoAnswerService(adb_engine, event_bus)
    auto_answer_enabled = answer_service._is_auto_answer_enabled()
    first_serial = next(iter(adb_engine.connected_devices.keys()), None)
    auto_answer_ready = (
        await answer_service.can_auto_answer(first_serial)
        if first_serial
        else False
    )

    return SuccessResponse(
        data={
            "database": {"status": db_status, "message": db_message},
            "redis": {"status": redis_status, "message": redis_message},
            "adb": adb_health,
            "devices": {
                "connected": device_sync.connected_count,
                "adb_found": device_sync.adb_devices_found,
            },
            "workers": get_worker_status(),
            "websocket": {
                "active_connections": ws_manager.active_connections,
            },
            "call_detection": {
                "poll_interval_seconds": settings.CALL_POLL_INTERVAL_SECONDS,
            },
            "auto_answer": {
                "enabled": auto_answer_enabled,
                "device_ready": bool(adb_engine.connected_devices),
                "can_answer": auto_answer_ready,
            },
            "ai": {
                "provider": settings.AI_ANALYSIS_PROVIDER,
                "configured": bool(settings.AI_ANALYSIS_API_KEY),
            },
        }
    )


@router.get("/info")
def system_info() -> SuccessResponse[dict]:
    return SuccessResponse(
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "description": settings.PROJECT_DESCRIPTION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        }
    )
