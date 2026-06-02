from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.system_log_repository import SystemLogRepository
from app.schemas.system_log import SystemLogRead


class LogService:
    def __init__(self, db: Session) -> None:
        self.log_repo = SystemLogRepository(db)

    def get_log(self, log_id: int) -> SystemLogRead:
        log = self.log_repo.get_by_id(log_id)
        if not log:
            raise NotFoundException("Log not found")
        return SystemLogRead.model_validate(log)

    def get_recent_logs(self, limit: int = 100) -> list[SystemLogRead]:
        logs = self.log_repo.get_recent_logs(limit=limit)
        return [SystemLogRead.model_validate(l) for l in logs]

    def get_logs_by_level(self, level: str, limit: int = 100) -> list[SystemLogRead]:
        logs = self.log_repo.get_by_level(level, limit=limit)
        return [SystemLogRead.model_validate(l) for l in logs]

    def get_logs_by_module(self, module: str, limit: int = 100) -> list[SystemLogRead]:
        logs = self.log_repo.get_by_module(module, limit=limit)
        return [SystemLogRead.model_validate(l) for l in logs]

    def create_log(
        self, level: str, module: str, message: str, metadata_json: str | None = None
    ) -> SystemLogRead:
        log = self.log_repo.create_log(level, module, message, metadata_json)
        return SystemLogRead.model_validate(log)

    def get_log_count(self) -> int:
        return self.log_repo.count()
