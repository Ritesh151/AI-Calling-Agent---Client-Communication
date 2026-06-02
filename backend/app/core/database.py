from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

_use_sqlite = os.environ.get("USE_SQLITE", "").lower() in ("true", "1", "yes")


def _try_pg_connect() -> bool:
    if _use_sqlite:
        return False
    try:
        test_engine = create_engine(
            str(settings.DATABASE_URL),
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
            echo=False,
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        logger.info("PostgreSQL connection OK at %s", settings.DATABASE_URL)
        return True
    except Exception as e:
        logger.warning("PostgreSQL unreachable at %s: %s", settings.DATABASE_URL, e)
        return False


_use_pg = _try_pg_connect()

if _use_pg:
    engine = create_engine(
        str(settings.DATABASE_URL),
        pool_pre_ping=True,
        pool_size=settings.SERVER_WORKERS * 2,
        max_overflow=10,
        echo=settings.DEBUG,
    )
    logger.info("Using PostgreSQL database")
else:
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "app.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
    logger.info("Using SQLite database at %s", db_path)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: type[Any] = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
