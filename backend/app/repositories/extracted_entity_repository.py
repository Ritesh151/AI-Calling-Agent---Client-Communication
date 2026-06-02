from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.extracted_entity import ExtractedEntity
from app.repositories.base import BaseRepository


class ExtractedEntityRepository(BaseRepository[ExtractedEntity]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ExtractedEntity)

    def get_by_session(self, call_session_id: int) -> list[ExtractedEntity]:
        return (
            self.db.query(ExtractedEntity)
            .filter(ExtractedEntity.call_session_id == call_session_id)
            .all()
        )

    def get_by_type(self, entity_type: str) -> list[ExtractedEntity]:
        return (
            self.db.query(ExtractedEntity)
            .filter(ExtractedEntity.entity_type == entity_type)
            .all()
        )

    def get_by_value(self, value: str) -> list[ExtractedEntity]:
        return (
            self.db.query(ExtractedEntity)
            .filter(ExtractedEntity.entity_value.ilike(f"%{value}%"))
            .all()
        )

    def get_distinct_types(self) -> list[str]:
        results = self.db.query(ExtractedEntity.entity_type).distinct().all()
        return [r[0] for r in results]
