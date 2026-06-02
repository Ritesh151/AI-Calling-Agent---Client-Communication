from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChromaDBProvider:
    def __init__(self) -> None:
        self._client = None
        self._collection = None
        self._collection_name = "call_embeddings"

    def _ensure_initialized(self):
        if self._collection is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=settings.EMBEDDING_CHROMA_PATH)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def store_embedding(self, vector_id: str, embedding: list[float], metadata: dict) -> str:
        self._ensure_initialized()
        self._collection.add(
            ids=[vector_id],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        return vector_id

    def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict[str, Any]]:
        self._ensure_initialized()
        where = filters or None
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
        )
        output = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "score": results["distances"][0][i] if results.get("distances") else 0,
                    "metadata": (results["metadatas"][0][i] if results.get("metadatas") else {}),
                })
        return output

    def delete(self, vector_id: str) -> bool:
        self._ensure_initialized()
        self._collection.delete(ids=[vector_id])
        return True

    def delete_by_session(self, call_session_id: int) -> int:
        self._ensure_initialized()
        results = self._collection.get(where={"call_session_id": call_session_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0

    def count(self) -> int:
        self._ensure_initialized()
        return self._collection.count()

    def health_check(self) -> bool:
        try:
            self._ensure_initialized()
            self._collection.count()
            return True
        except Exception:
            return False
