from __future__ import annotations

from typing import Any

_worker_status: dict[str, dict[str, Any]] = {}


def set_worker_status(name: str, *, running: bool, detail: str | None = None) -> None:
    _worker_status[name] = {
        "running": running,
        "detail": detail or ("active" if running else "stopped"),
    }


def get_worker_status() -> dict[str, dict[str, Any]]:
    return dict(_worker_status)
