from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoStorage:
    def __init__(self) -> None:
        self._client: Any | None = None
        self._disabled = not settings.MONGODB_ENABLED

    def _db(self) -> Any | None:
        if self._disabled:
            return None
        if self._client is None:
            try:
                from pymongo import MongoClient

                self._client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=1000)
                self._client.admin.command("ping")
            except Exception as exc:
                self._disabled = True
                logger.warning("MongoDB unavailable; SQL storage remains active: %s", exc)
                return None
        return self._client[settings.MONGODB_DB]

    def upsert_call_document(self, document: dict[str, Any]) -> None:
        db = self._db()
        if db is None:
            return
        document["updated_at"] = datetime.utcnow().isoformat()
        db.call_sessions.update_one(
            {"call_id": document["call_id"]},
            {"$set": document, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
            upsert=True,
        )

    def create_client_database(self, db_name: str, payload: dict[str, Any]) -> None:
        if self._disabled:
            return
        if self._client is None:
            self._db()
        if self._client is None:
            return

        client_db = self._client[db_name]
        payload["updated_at"] = datetime.utcnow().isoformat()
        client_db.call_sessions.update_one(
            {"call_id": payload["call_id"]},
            {"$set": payload, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
            upsert=True,
        )

    def upsert_project_document(self, document: dict[str, Any]) -> None:
        db = self._db()
        if db is None:
            return
        document["updated_at"] = datetime.utcnow().isoformat()
        db.project_documents.update_one(
            {"project_id": document["project_id"]},
            {"$set": document, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
            upsert=True,
        )

    def upsert_proposal_document(self, document: dict[str, Any]) -> None:
        db = self._db()
        if db is None:
            return
        document["updated_at"] = datetime.utcnow().isoformat()
        db.project_proposals.update_one(
            {"project_id": document["project_id"]},
            {"$set": document, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
            upsert=True,
        )

    def get_project_document(self, project_id: int) -> dict[str, Any] | None:
        db = self._db()
        if db is None:
            return None
        return db.project_documents.find_one({"project_id": project_id}, {"_id": 0})

    def get_project_proposal(self, project_id: int) -> dict[str, Any] | None:
        db = self._db()
        if db is None:
            return None
        return db.project_proposals.find_one({"project_id": project_id}, {"_id": 0})

    def list_project_proposals(self, limit: int = 100) -> list[dict[str, Any]]:
        db = self._db()
        if db is None:
            return []
        return list(db.project_proposals.find({}, {"_id": 0}).limit(limit))

    def list_project_documents(self, limit: int = 100) -> list[dict[str, Any]]:
        db = self._db()
        if db is None:
            return []
        return list(db.project_documents.find({}, {"_id": 0}).limit(limit))


mongo_storage = MongoStorage()
