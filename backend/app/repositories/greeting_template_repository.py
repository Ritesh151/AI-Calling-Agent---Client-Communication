from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.greeting_template import GreetingTemplate
from app.repositories.base import BaseRepository


class GreetingTemplateRepository(BaseRepository[GreetingTemplate]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, GreetingTemplate)

    def get_default(self, language: str | None = None) -> GreetingTemplate | None:
        if language:
            return (
                self.db.query(GreetingTemplate)
                .filter(
                    GreetingTemplate.is_default.is_(True),
                    GreetingTemplate.language == language,
                )
                .first()
            )
        return (
            self.db.query(GreetingTemplate)
            .filter(GreetingTemplate.is_default.is_(True))
            .first()
        )

    def get_by_language(self, language: str) -> list[GreetingTemplate]:
        return (
            self.db.query(GreetingTemplate)
            .filter(GreetingTemplate.language == language)
            .all()
        )
