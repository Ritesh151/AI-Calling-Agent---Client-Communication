from __future__ import annotations

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    password = "TestPass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass!", hashed)


def test_access_token_creation() -> None:
    token = create_access_token(subject="1")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "access"


def test_refresh_token_creation() -> None:
    token = create_refresh_token(subject="1")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"


def test_invalid_token() -> None:
    payload = decode_token("invalid_token_here")
    assert payload == {}
