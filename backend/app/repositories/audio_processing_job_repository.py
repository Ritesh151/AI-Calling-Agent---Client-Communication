from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.audio_processing_job import AudioProcessingJob
from app.repositories.base import BaseRepository


class AudioProcessingJobRepository(BaseRepository[AudioProcessingJob]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AudioProcessingJob)

    def get_by_recording(self, recording_id: int) -> list[AudioProcessingJob]:
        return (
            self.db.query(AudioProcessingJob)
            .filter(AudioProcessingJob.recording_id == recording_id)
            .all()
        )

    def get_by_status(self, status: str) -> list[AudioProcessingJob]:
        return (
            self.db.query(AudioProcessingJob)
            .filter(AudioProcessingJob.status == status)
            .all()
        )

    def get_pending_jobs(self, limit: int = 10) -> list[AudioProcessingJob]:
        return (
            self.db.query(AudioProcessingJob)
            .filter(AudioProcessingJob.status == "pending")
            .limit(limit)
            .all()
        )
