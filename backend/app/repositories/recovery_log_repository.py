from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.recovery_log_model import RecoveryLog
from app.repositories.base import BaseRepository


class RecoveryLogRepository(BaseRepository[RecoveryLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RecoveryLog)

    def get_by_device(self, device_id: int, limit: int | None = None) -> list[RecoveryLog]:
        query = (
            self.db.query(RecoveryLog)
            .filter(RecoveryLog.device_id == device_id)
            .order_by(RecoveryLog.created_at.desc())
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_status(self, status: str) -> list[RecoveryLog]:
        return (
            self.db.query(RecoveryLog)
            .filter(RecoveryLog.status == status)
            .all()
        )

    def get_failed_recoveries(self) -> list[RecoveryLog]:
        return (
            self.db.query(RecoveryLog)
            .filter(RecoveryLog.status == "failed")
            .all()
        )

    def get_recovery_success_rate(self, device_id: int) -> float:
        total = self.db.query(RecoveryLog).filter(
            RecoveryLog.device_id == device_id
        ).count()
        if total == 0:
            return 1.0
        success = self.db.query(RecoveryLog).filter(
            RecoveryLog.device_id == device_id,
            RecoveryLog.status == "completed",
        ).count()
        return success / total
