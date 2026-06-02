from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.call_summary import CallSummary
from app.repositories.base import BaseRepository


class CallSummaryRepository(BaseRepository[CallSummary]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CallSummary)

    def get_by_session(self, call_session_id: int) -> CallSummary | None:
        return (
            self.db.query(CallSummary)
            .filter(CallSummary.call_session_id == call_session_id)
            .first()
        )

    def get_by_urgency(self, urgency: str) -> list[CallSummary]:
        return (
            self.db.query(CallSummary)
            .filter(CallSummary.urgency_level == urgency)
            .all()
        )

    def get_by_callback_status(self, status: str) -> list[CallSummary]:
        return (
            self.db.query(CallSummary)
            .filter(CallSummary.callback_required == status)
            .all()
        )

    def get_unprocessed(self) -> list[CallSummary]:
        return (
            self.db.query(CallSummary)
            .filter(CallSummary.summary.is_(None))
            .all()
        )
