from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.call_session import CallSession
from app.repositories.base import BaseRepository


class CallSessionRepository(BaseRepository[CallSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CallSession)

    def get_by_device(self, device_id: int) -> list[CallSession]:
        return (
            self.db.query(CallSession)
            .filter(CallSession.device_id == device_id)
            .order_by(CallSession.created_at.desc())
            .all()
        )

    def get_active_sessions(self) -> list[CallSession]:
        return (
            self.db.query(CallSession)
            .filter(CallSession.call_status.in_(["pending", "ringing", "answering", "active"]))
            .all()
        )

    def get_recent_sessions(self, limit: int = 50) -> list[CallSession]:
        return (
            self.db.query(CallSession)
            .order_by(CallSession.created_at.desc())
            .limit(limit)
            .all()
        )
