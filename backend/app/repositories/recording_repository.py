from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.recording import Recording
from app.repositories.base import BaseRepository


class RecordingRepository(BaseRepository[Recording]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Recording)

    def get_by_call_session(self, call_session_id: int) -> list[Recording]:
        return (
            self.db.query(Recording)
            .filter(Recording.call_session_id == call_session_id)
            .all()
        )

    def get_by_status(self, status: str) -> list[Recording]:
        return (
            self.db.query(Recording)
            .filter(Recording.recording_status == status)
            .all()
        )

    def get_by_device_and_status(self, device_id: int, status: str) -> list[Recording]:
        return (
            self.db.query(Recording)
            .filter(Recording.device_id == device_id, Recording.recording_status == status)
            .all()
        )

    def get_total_storage_size(self) -> int:
        result = self.db.query(Recording.file_size).filter(Recording.file_size.isnot(None)).all()
        return sum(r[0] for r in result if r[0]) if result else 0
