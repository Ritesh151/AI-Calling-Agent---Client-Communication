from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript
from app.repositories.ai_processing_job_repository import AIProcessingJobRepository
from app.services.ai_analysis.classification.classification_service import (
    ClassificationService,
)
from app.services.ai_analysis.entity_extraction.entity_extraction_service import (
    EntityExtractionService,
)
from app.services.ai_analysis.sentiment.sentiment_service import SentimentService
from app.services.ai_analysis.urgency.urgency_service import UrgencyService

logger = logging.getLogger(__name__)


class ClassificationWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Classification worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Classification worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                logger.error("Classification worker error: %s", e)
            await asyncio.sleep(15)

    def _process_pending(self) -> None:
        db = SessionLocal()
        try:
            repo = AIProcessingJobRepository(db)
            jobs = repo.get_pending(limit=10)
            for job in db.query(Transcript).filter(
                Transcript.transcript_text.isnot(None),
                Transcript.confidence_score.isnot(None),
            ).limit(5).all():
                csid = job.recording_id
                if not repo.get_by_type_and_status("classification", "pending") and \
                   not repo.get_by_type_and_status("classification", "processing"):
                    repo.create(call_session_id=csid, job_type="classification")

            cjobs = repo.get_by_type_and_status("classification", "pending")
            for job in cjobs:
                try:
                    repo.mark_started(job.id)
                    recording = db.query(Recording).filter(
                        Recording.call_session_id == job.call_session_id
                    ).first()
                    transcript = None
                    if recording:
                        transcript = db.query(Transcript).filter(
                            Transcript.recording_id == recording.id
                        ).first()
                    if transcript and transcript.transcript_text:
                        text = transcript.transcript_text
                        ClassificationService().classify(text)
                        SentimentService().analyze_sentiment(text)
                        UrgencyService().detect_urgency(text)
                        EntityExtractionService().extract_entities(text)
                        repo.mark_completed(job.id)
                except Exception as e:
                    repo.mark_failed(job.id, str(e))
        finally:
            db.close()
