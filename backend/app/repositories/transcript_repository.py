from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.transcript import Transcript
from app.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository[Transcript]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Transcript)

    def get_by_recording(self, recording_id: int) -> Transcript | None:
        return (
            self.db.query(Transcript)
            .filter(Transcript.recording_id == recording_id)
            .first()
        )

    def get_by_confidence_range(self, min_score: float, max_score: float) -> list[Transcript]:
        return (
            self.db.query(Transcript)
            .filter(Transcript.confidence_score.between(min_score, max_score))
            .all()
        )
