from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.call_classification_model import CallClassification
from app.repositories.base import BaseRepository


class CallClassificationRepository(BaseRepository[CallClassification]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CallClassification)

    def get_by_session(self, call_session_id: int) -> list[CallClassification]:
        return (
            self.db.query(CallClassification)
            .filter(CallClassification.call_session_id == call_session_id)
            .all()
        )

    def get_by_category(self, category: str) -> list[CallClassification]:
        return (
            self.db.query(CallClassification)
            .filter(CallClassification.category == category)
            .all()
        )

    def get_primary_by_session(self, call_session_id: int) -> CallClassification | None:
        return (
            self.db.query(CallClassification)
            .filter(CallClassification.call_session_id == call_session_id)
            .order_by(CallClassification.confidence_score.desc())
            .first()
        )

    def get_distinct_categories(self) -> list[str]:
        results = self.db.query(CallClassification.category).distinct().all()
        return [r[0] for r in results]
