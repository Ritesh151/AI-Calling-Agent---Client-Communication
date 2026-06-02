from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.compatibility_report_model import CompatibilityReport
from app.repositories.base import BaseRepository


class CompatibilityReportRepository(BaseRepository[CompatibilityReport]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CompatibilityReport)

    def get_by_device(self, device_id: int) -> list[CompatibilityReport]:
        return (
            self.db.query(CompatibilityReport)
            .filter(CompatibilityReport.device_id == device_id)
            .order_by(CompatibilityReport.created_at.desc())
            .all()
        )

    def get_by_type(self, report_type: str) -> list[CompatibilityReport]:
        return (
            self.db.query(CompatibilityReport)
            .filter(CompatibilityReport.report_type == report_type)
            .all()
        )

    def get_latest_by_device(self, device_id: int) -> CompatibilityReport | None:
        return (
            self.db.query(CompatibilityReport)
            .filter(CompatibilityReport.device_id == device_id)
            .order_by(CompatibilityReport.created_at.desc())
            .first()
        )
