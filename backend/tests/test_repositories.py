from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.user_repository import UserRepository


def test_create_user(db_session: Session) -> None:
    repo = UserRepository(db_session)
    user = repo.create(
        email="new@example.com",
        username="newuser",
        password_hash="hashed_password",
        role="user",
        is_active=True,
    )
    assert user.id is not None
    assert user.email == "new@example.com"


def test_get_by_email(db_session: Session, test_user: User) -> None:
    repo = UserRepository(db_session)
    found = repo.get_by_email("test@example.com")
    assert found is not None
    assert found.username == "testuser"


def test_get_by_id(db_session: Session, test_user: User) -> None:
    repo = UserRepository(db_session)
    found = repo.get_by_id(test_user.id)
    assert found is not None
    assert found.email == "test@example.com"


def test_update_user(db_session: Session, test_user: User) -> None:
    repo = UserRepository(db_session)
    updated = repo.update(test_user.id, username="updateduser")
    assert updated is not None
    assert updated.username == "updateduser"


def test_delete_user(db_session: Session, test_user: User) -> None:
    repo = UserRepository(db_session)
    result = repo.delete(test_user.id)
    assert result is True
    assert repo.get_by_id(test_user.id) is None
