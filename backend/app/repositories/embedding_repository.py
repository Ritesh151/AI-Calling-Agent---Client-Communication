from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.embedding_model import EmbeddingRecord
from app.repositories.base import BaseRepository


class EmbeddingRepository(BaseRepository[EmbeddingRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EmbeddingRecord)

    def get_by_session(self, call_session_id: int) -> list[EmbeddingRecord]:
        return (
            self.db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.call_session_id == call_session_id)
            .all()
        )

    def get_by_vector_id(self, vector_id: str) -> EmbeddingRecord | None:
        return (
            self.db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.vector_id == vector_id)
            .first()
        )

    def get_by_provider(self, provider: str) -> list[EmbeddingRecord]:
        return (
            self.db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.embedding_provider == provider)
            .all()
        )

    def delete_by_session(self, call_session_id: int) -> int:
        count = (
            self.db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.call_session_id == call_session_id)
            .delete()
        )
        self.db.commit()
        return count

    def count_by_provider(self) -> dict[str, int]:
        from sqlalchemy import func
        results = (
            self.db.query(
                EmbeddingRecord.embedding_provider,
                func.count(EmbeddingRecord.id),
            )
            .group_by(EmbeddingRecord.embedding_provider)
            .all()
        )
        return {r[0]: r[1] for r in results}
