from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.audio_processing_job import AudioProcessingJob
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript

logger = logging.getLogger(__name__)


class ArchiveService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def archive_expired_recordings(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_RECORDING_DAYS)
        recordings = (
            self.db.query(Recording)
            .filter(Recording.created_at < cutoff)
            .all()
        )

        archived_count = 0
        for recording in recordings:
            try:
                file_path = Path(recording.file_path)
                if file_path.exists():
                    archive_path = file_path.parent / "archived" / file_path.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(archive_path))
                    recording.file_path = str(archive_path)
                    recording.recording_status = "archived"
                    archived_count += 1
            except Exception as e:
                logger.error("Failed to archive recording %d: %s", recording.id, e)

        self.db.commit()
        logger.info("Archived %d recordings", archived_count)
        return archived_count

    def delete_expired_recordings(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_RECORDING_DAYS)
        recordings = (
            self.db.query(Recording)
            .filter(Recording.created_at < cutoff)
            .all()
        )

        deleted_count = 0
        for recording in recordings:
            try:
                file_path = Path(recording.file_path)
                if file_path.exists():
                    file_path.unlink()
                self.db.query(Transcript).filter(Transcript.recording_id == recording.id).delete()
                self.db.query(AudioProcessingJob).filter(
                    AudioProcessingJob.recording_id == recording.id
                ).delete()
                self.db.delete(recording)
                deleted_count += 1
            except Exception as e:
                logger.error("Failed to delete recording %d: %s", recording.id, e)

        self.db.commit()
        logger.info("Permanently deleted %d expired recordings", deleted_count)
        return deleted_count

    def get_storage_stats(self) -> dict:
        recordings = self.db.query(Recording).all()
        total_size = 0
        status_counts: dict[str, int] = {}
        for r in recordings:
            if r.file_size:
                total_size += r.file_size
            status_counts[r.recording_status] = status_counts.get(r.recording_status, 0) + 1

        return {
            "total_recordings": len(recordings),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
            "status_breakdown": status_counts,
            "retention_days": settings.RETENTION_RECORDING_DAYS,
            "auto_cleanup": settings.RETENTION_AUTO_CLEANUP,
            "archive_enabled": settings.RETENTION_ARCHIVE_ENABLED,
        }
