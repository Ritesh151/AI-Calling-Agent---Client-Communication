from __future__ import annotations

import asyncio
import logging

from app.core.database import SessionLocal
from app.repositories.audio_processing_job_repository import AudioProcessingJobRepository
from app.repositories.recording_repository import RecordingRepository
from app.services.transcription.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)


class AudioProcessingWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Audio processing worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Audio processing worker stopped")

    async def _run(self) -> None:
        while self._running:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self._process_pending_jobs)
            except Exception as e:
                logger.error("Audio processing error: %s", e)
            await asyncio.sleep(5)

    def _process_pending_jobs(self) -> None:
        db = SessionLocal()
        try:
            repo = AudioProcessingJobRepository(db)
            jobs = repo.get_pending_jobs(limit=5)

            for job in jobs:
                try:
                    if job.job_type == "transcription":
                        recording_repo = RecordingRepository(db)
                        recording = recording_repo.get_by_id(job.recording_id)
                        if recording and recording.recording_status == "completed":
                            service = TranscriptionService(db)
                            service.transcribe_recording(job.recording_id)
                            logger.info("Processed transcription job %d", job.id)
                except Exception as e:
                    logger.error("Failed to process job %d: %s", job.id, e)
        finally:
            db.close()
