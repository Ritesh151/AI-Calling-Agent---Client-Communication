from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models.system_log import SystemLog
from app.repositories.base import BaseRepository


class SystemLogRepository(BaseRepository[SystemLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SystemLog)

    def get_by_level(self, level: str, limit: int = 100) -> list[SystemLog]:
        return (
            self.db.query(SystemLog)
            .filter(SystemLog.level == level.upper())
            .order_by(SystemLog.logged_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_module(self, module: str, limit: int = 100) -> list[SystemLog]:
        return (
            self.db.query(SystemLog)
            .filter(SystemLog.module == module)
            .order_by(SystemLog.logged_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_logs(self, limit: int = 100) -> list[SystemLog]:
        return (
            self.db.query(SystemLog)
            .order_by(SystemLog.logged_at.desc())
            .limit(limit)
            .all()
        )

    def get_logs_in_range(
        self, start: datetime, end: datetime, limit: int = 1000
    ) -> list[SystemLog]:
        return (
            self.db.query(SystemLog)
            .filter(SystemLog.logged_at.between(start, end))
            .order_by(SystemLog.logged_at.desc())
            .limit(limit)
            .all()
        )

    def create_log(
        self, level: str, module: str, message: str, metadata_json: str | None = None
    ) -> SystemLog:
        return self.create(
            level=level.upper(),
            module=module,
            message=message,
            metadata_json=metadata_json,
            logged_at=datetime.now(UTC),
        )
