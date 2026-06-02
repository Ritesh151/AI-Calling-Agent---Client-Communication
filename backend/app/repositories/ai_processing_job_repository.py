from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.ai_processing_job_model import AIProcessingJob
from app.repositories.base import BaseRepository


class AIProcessingJobRepository(BaseRepository[AIProcessingJob]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AIProcessingJob)

    def get_by_session(self, call_session_id: int) -> list[AIProcessingJob]:
        return (
            self.db.query(AIProcessingJob)
            .filter(AIProcessingJob.call_session_id == call_session_id)
            .all()
        )

    def get_by_type(self, job_type: str) -> list[AIProcessingJob]:
        return (
            self.db.query(AIProcessingJob)
            .filter(AIProcessingJob.job_type == job_type)
            .all()
        )

    def get_by_type_and_status(self, job_type: str, status: str) -> list[AIProcessingJob]:
        return (
            self.db.query(AIProcessingJob)
            .filter(
                AIProcessingJob.job_type == job_type,
                AIProcessingJob.status == status,
            )
            .all()
        )

    def get_pending(self, limit: int = 20) -> list[AIProcessingJob]:
        return (
            self.db.query(AIProcessingJob)
            .filter(AIProcessingJob.status == "pending")
            .limit(limit)
            .all()
        )

    def mark_started(self, job_id: int) -> None:
        job = self.get_by_id(job_id)
        if job:
            job.status = "processing"
            job.started_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_completed(self, job_id: int) -> None:
        job = self.get_by_id(job_id)
        if job:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_failed(self, job_id: int, error: str) -> None:
        job = self.get_by_id(job_id)
        if job:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = error
            self.db.commit()
