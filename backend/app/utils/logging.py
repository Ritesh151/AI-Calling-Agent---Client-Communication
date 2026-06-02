from __future__ import annotations

import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
        },
    }

    if settings.LOG_FILE_ENABLED:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "app.log"),
            "maxBytes": settings.LOG_FILE_MAX_BYTES,
            "backupCount": settings.LOG_FILE_BACKUP_COUNT,
            "formatter": "json",
        }

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": handlers,
        "root": {
            "level": log_level,
            "handlers": list(handlers.keys()),
        },
        "loggers": {
            "uvicorn": {"level": log_level, "handlers": list(handlers.keys()), "propagate": False},
            "uvicorn.access": {"level": log_level, "handlers": list(handlers.keys()), "propagate": False},
            "sqlalchemy": {"level": logging.WARNING, "handlers": list(handlers.keys()), "propagate": False},
            "app": {"level": log_level, "handlers": list(handlers.keys()), "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)
