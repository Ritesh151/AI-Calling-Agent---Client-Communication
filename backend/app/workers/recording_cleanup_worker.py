from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.call_archive.archive_service import ArchiveService

logger = logging.getLogger(__name__)


class RecordingCleanupWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not settings.RETENTION_AUTO_CLEANUP:
            logger.info("Recording cleanup worker disabled by config")
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Recording cleanup worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Recording cleanup worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self._cleanup)
            except Exception as e:
                logger.error("Recording cleanup error: %s", e)
            await asyncio.sleep(settings.RETENTION_CLEANUP_INTERVAL_HOURS * 3600)

    def _cleanup(self) -> None:
        db = SessionLocal()
        try:
            archive_service = ArchiveService(db)
            if settings.RETENTION_ARCHIVE_ENABLED:
                archived = archive_service.archive_expired_recordings()
                if archived:
                    logger.info("Archived %d recordings", archived)
            deleted = archive_service.delete_expired_recordings()
            if deleted:
                logger.info("Deleted %d expired recordings", deleted)
        finally:
            db.close()
