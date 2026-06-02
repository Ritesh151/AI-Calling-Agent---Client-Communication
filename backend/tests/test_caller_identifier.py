from __future__ import annotations

from app.services.call_detector.caller_identifier import CallerIdentifier


def test_standard_number() -> None:
    info = CallerIdentifier.identify("+15551234567")
    assert info.caller_number == "+15551234567"
    assert info.caller_type == "external"
    assert info.country_code == "1"


def test_private_number() -> None:
    info = CallerIdentifier.identify("private")
    assert info.caller_type == "private"
    assert info.caller_name == "Private Number"


def test_unknown_number() -> None:
    info = CallerIdentifier.identify("unknown")
    assert info.caller_type == "private"
    assert info.caller_name == "Private Number"


def test_international_number() -> None:
    info = CallerIdentifier.identify("+919876543210")
    assert info.country_code == "91"
    assert info.normalized_number == "+919876543210"


def test_empty_number() -> None:
    info = CallerIdentifier.identify("")
    assert info.caller_type == "unknown"
    assert info.caller_name == "Unknown"


def test_normalize_number() -> None:
    normalized = CallerIdentifier._normalize_number("+1 (555) 123-4567")
    assert normalized == "+15551234567"


def test_normalize_international_prefix() -> None:
    normalized = CallerIdentifier._normalize_number("0044123456789")
    assert normalized == "+44123456789"
