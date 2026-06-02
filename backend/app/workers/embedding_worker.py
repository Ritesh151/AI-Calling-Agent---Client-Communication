from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript
from app.services.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Embedding worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Embedding worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                logger.error("Embedding worker error: %s", e)
            await asyncio.sleep(20)

    def _process_pending(self) -> None:
        db = SessionLocal()
        try:
            from app.db.models.embedding_model import EmbeddingRecord
            transcribed = db.query(Transcript).filter(
                Transcript.transcript_text.isnot(None),
                Transcript.confidence_score.isnot(None),
            ).all()

            for t in transcribed:
                recording = db.query(Recording).filter(
                    Recording.id == t.recording_id
                ).first()
                csid = recording.call_session_id if recording else t.recording_id
                existing = db.query(EmbeddingRecord).filter(
                    EmbeddingRecord.call_session_id == csid
                ).first()
                if not existing:
                    try:
                        svc = EmbeddingService(db)
                        svc.generate_embeddings(csid, t.transcript_text)
                        logger.info("Generated embeddings for call %d", csid)
                        logger.info("Generated embeddings for call %d", t.recording_id)
                    except Exception as e:
                        logger.error("Failed to embed call %d: %s", t.recording_id, e)
        finally:
            db.close()
