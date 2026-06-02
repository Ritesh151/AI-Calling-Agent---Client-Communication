from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class CallerInfo:
    caller_number: str = ""
    caller_name: str = ""
    caller_type: str = "unknown"
    country_code: str = ""
    normalized_number: str = ""
    raw_data: str = ""
    detected_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


class CallerIdentifier:
    PRIVATE_PATTERNS = [
        re.compile(r"private", re.I),
        re.compile(r"unknown", re.I),
        re.compile(r"blocked", re.I),
        re.compile(r"hidden", re.I),
        re.compile(r"restricted", re.I),
        re.compile(r"withheld", re.I),
        re.compile(r"^\-?1$"),
        re.compile(r"^0$"),
    ]

    NUMBER_PATTERN = re.compile(r"\+?\d[\d\s\-\.\(\)]{4,20}\d")

    @classmethod
    def identify(cls, raw_number: str, raw_data: str = "") -> CallerInfo:
        info = CallerInfo(raw_data=raw_data)

        if not raw_number or raw_number.strip() == "":
            info.caller_number = ""
            info.caller_name = "Unknown"
            info.caller_type = "unknown"
            return info

        cleaned = raw_number.strip()

        if cls._is_private(cleaned):
            info.caller_number = "private"
            info.caller_name = "Private Number"
            info.caller_type = "private"
            return info

        number_match = cls.NUMBER_PATTERN.search(cleaned)
        if number_match:
            info.caller_number = number_match.group()
        else:
            info.caller_number = cleaned

        info.normalized_number = cls._normalize_number(info.caller_number)
        info.country_code = cls._detect_country_code(info.caller_number)

        if info.caller_number:
            info.caller_type = "external"
            info.caller_name = info.caller_number
        else:
            info.caller_type = "unknown"
            info.caller_name = "Unknown"

        return info

    @classmethod
    def _is_private(cls, number: str) -> bool:
        for pattern in cls.PRIVATE_PATTERNS:
            if pattern.search(number):
                return True
        return False

    @classmethod
    def _normalize_number(cls, number: str) -> str:
        cleaned = re.sub(r"[^\d+]", "", number)
        if cleaned.startswith("+"):
            return cleaned
        if cleaned.startswith("00"):
            return "+" + cleaned[2:]
        return cleaned

    @classmethod
    def _detect_country_code(cls, number: str) -> str:
        normalized = cls._normalize_number(number)
        if normalized.startswith("+1"):
            return "1"
        elif normalized.startswith("+44"):
            return "44"
        elif normalized.startswith("+91"):
            return "91"
        elif normalized.startswith("+86"):
            return "86"
        elif normalized.startswith("+49"):
            return "49"
        elif normalized.startswith("+33"):
            return "33"
        elif normalized.startswith("+81"):
            return "81"
        elif normalized.startswith("+61"):
            return "61"
        return ""
