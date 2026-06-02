from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.call_session_repository import CallSessionRepository
from app.schemas.call_session import (
    CallSessionCreate,
    CallSessionRead,
    CallSessionUpdate,
)


class CallSessionService:
    def __init__(self, db: Session) -> None:
        self.session_repo = CallSessionRepository(db)

    def create_session(self, request: CallSessionCreate) -> CallSessionRead:
        session = self.session_repo.create(**request.model_dump())
        return CallSessionRead.model_validate(session)

    def get_session(self, session_id: int) -> CallSessionRead:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException("Call session not found")
        return CallSessionRead.model_validate(session)

    def get_all_sessions(
        self, skip: int = 0, limit: int = 100
    ) -> list[CallSessionRead]:
        sessions = self.session_repo.get_all(
            skip=skip, limit=limit, order_by="created_at", order_desc=True
        )
        return [CallSessionRead.model_validate(s) for s in sessions]

    def update_session(
        self, session_id: int, request: CallSessionUpdate
    ) -> CallSessionRead:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException("Call session not found")
        update_data = request.model_dump(exclude_unset=True)
        updated = self.session_repo.update(session_id, **update_data)
        return CallSessionRead.model_validate(updated)

    def get_device_sessions(self, device_id: int) -> list[CallSessionRead]:
        sessions = self.session_repo.get_by_device(device_id)
        return [CallSessionRead.model_validate(s) for s in sessions]

    def get_active_sessions(self) -> list[CallSessionRead]:
        sessions = self.session_repo.get_active_sessions()
        return [CallSessionRead.model_validate(s) for s in sessions]

    def get_session_count(self) -> int:
        return self.session_repo.count()

    def get_active_session_count(self) -> int:
        return len(self.session_repo.get_active_sessions())
