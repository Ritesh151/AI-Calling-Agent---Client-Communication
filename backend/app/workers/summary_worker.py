from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript
from app.repositories.ai_processing_job_repository import AIProcessingJobRepository
from app.services.ai_analysis.analysis_orchestrator import AnalysisOrchestrator

logger = logging.getLogger(__name__)


class SummaryWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Summary worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Summary worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                logger.error("Summary worker error: %s", e)
            await asyncio.sleep(10)

    def _process_pending(self) -> None:
        db = SessionLocal()
        try:
            repo = AIProcessingJobRepository(db)
            jobs = repo.get_by_type_and_status("full_analysis", "pending")
            for job in jobs:
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
                        orchestrator = AnalysisOrchestrator(db)
                        orchestrator.analyze_call(job.call_session_id, transcript.transcript_text)
                        repo.mark_completed(job.id)
                        logger.info("Summary completed for call %d", job.call_session_id)
                    else:
                        repo.mark_failed(job.id, "No transcript available")
                except Exception as e:
                    repo.mark_failed(job.id, str(e))
                    logger.error("Summary job %d failed: %s", job.id, e)
        finally:
            db.close()
