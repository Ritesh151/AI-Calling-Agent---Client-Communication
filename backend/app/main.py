from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import AppException
from app.middlewares.cors import setup_cors
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.services.adb_watcher import adb_engine
from app.services.event_bus import event_bus
from app.services.websocket import ws_manager
from app.utils.logging import setup_logging
from app.workers.registry import set_worker_status
from app.workers import (
    ADBWatcherWorker,
    AnalyticsWorker,
    AudioProcessingWorker,
    CallDetectionWorker,
    CallLifecycleWorker,
    ClassificationWorker,
    DeviceHeartbeatWorker,
    EmbeddingWorker,
    EventDispatcherWorker,
    InsightWorker,
    KnowledgeWorker,
    RecordingCleanupWorker,
    ReportWorker,
    SummaryWorker,
)

logger = logging.getLogger(__name__)

workers: list[Any] = []


def _ensure_phase1_columns() -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if not inspector.has_table("call_sessions"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("call_sessions")}
    if "language" in existing_columns:
        return

    dialect = engine.dialect.name
    column_type = "VARCHAR(20)" if dialect != "sqlite" else "VARCHAR(20)"
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE call_sessions ADD COLUMN language {column_type}"))
    logger.info("Added missing call_sessions.language column")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(
        "Starting %s v%s in %s mode",
        settings.PROJECT_NAME,
        settings.PROJECT_VERSION,
        settings.ENVIRONMENT,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_phase1_columns()

    await event_bus.start()

    worker_classes = [
        ADBWatcherWorker,
        DeviceHeartbeatWorker,
        CallDetectionWorker,
        CallLifecycleWorker,
        EventDispatcherWorker,
        AudioProcessingWorker,
        RecordingCleanupWorker,
        SummaryWorker,
        ClassificationWorker,
        EmbeddingWorker,
        KnowledgeWorker,
        AnalyticsWorker,
        InsightWorker,
        ReportWorker,
    ]
    for wc in worker_classes:
        try:
            worker = wc()
            await worker.start()
            workers.append(worker)
            set_worker_status(wc.__name__, running=True)
            logger.info("Started worker: %s", wc.__name__)
        except Exception as e:
            set_worker_status(wc.__name__, running=False, detail=str(e))
            logger.error("Failed to start worker %s: %s", wc.__name__, e)

    logger.info("All workers started. System ready.")

    try:
        from app.core.database import SessionLocal
        from app.services.device_sync import device_sync_service

        db = SessionLocal()
        try:
            result = await device_sync_service.sync(db)
            logger.info(
                "Startup device sync: connected=%d total=%d adb=%d",
                result.connected_count,
                result.total_registered,
                result.adb_devices_found,
            )
        finally:
            db.close()
    except Exception as e:
        logger.error("Startup device sync failed: %s", e)

    yield

    for worker in reversed(workers):
        try:
            await worker.stop()
        except Exception as e:
            logger.error("Error stopping worker: %s", e)

    await event_bus.stop()
    logger.info("Shutting down %s", settings.PROJECT_NAME)


_fastapi = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

setup_cors(_fastapi)

# Pure ASGI middleware — BaseHTTPMiddleware breaks WebSocket handshakes (Starlette)
_app: Any = _fastapi
_app = LoggingMiddleware(_app)
if settings.RATE_LIMIT_ENABLED:
    _app = RateLimitMiddleware(_app)
app = _app


_fastapi.include_router(api_router)


@_fastapi.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        },
    )


@_fastapi.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": {},
        },
    )


@_fastapi.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@_fastapi.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    client_id = id(websocket)
    try:
        await ws_manager.connect(websocket, client_id)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.strip().startswith("{"):
                import json

                try:
                    payload = json.loads(data)
                    if payload.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error: %s", e)
    finally:
        await ws_manager.disconnect(client_id)


@_fastapi.get("/health/database")
def health_database() -> dict[str, Any]:
    from sqlalchemy import text

    from app.core.database import SessionLocal

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


@_fastapi.get("/health/redis")
def health_redis() -> dict[str, Any]:
    try:
        import redis

        r = redis.Redis.from_url(str(settings.REDIS_URL))
        r.ping()
        return {"status": "healthy", "message": "Redis connection OK"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


@_fastapi.get("/health/adb")
async def health_adb() -> dict[str, Any]:
    try:
        health = await adb_engine.health_check()
        return {
            "status": "healthy" if health["is_healthy"] else "unhealthy",
            "server_running": health["server_running"],
            "devices_found": health["devices_found"],
        }
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


@_fastapi.get("/health/devices")
async def health_devices() -> dict[str, Any]:
    from app.core.database import SessionLocal
    from app.services.device_sync import device_sync_service

    try:
        db = SessionLocal()
        try:
            result = await device_sync_service.sync(db)
        finally:
            db.close()
        return {
            "status": "healthy",
            "total_devices": result.connected_count,
            "connected_devices": result.connected_count,
            "adb_devices_found": result.adb_devices_found,
        }
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
