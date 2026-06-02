from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.models.extracted_entity import ExtractedEntity
from app.db.models.call_summary import CallSummary
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class KnowledgeWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Knowledge worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Knowledge worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await self._update_index()
            except Exception as e:
                logger.error("Knowledge worker error: %s", e)
            await asyncio.sleep(300)

    async def _update_index(self) -> None:
        db = SessionLocal()
        try:
            entity_count = db.query(ExtractedEntity).count()
            summary_count = db.query(CallSummary).count()
            await event_bus.publish(Event(
                name="search_index_updated",
                data={
                    "entity_count": entity_count,
                    "summary_count": summary_count,
                    "timestamp": str(asyncio.get_event_loop().time()),
                },
                priority=EventPriority.LOW,
            ))
            logger.debug("Knowledge index updated: %d entities, %d summaries", entity_count, summary_count)
        finally:
            db.close()
