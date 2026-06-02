from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantProvider:
    def __init__(self) -> None:
        self._client = None
        self._collection_name = settings.EMBEDDING_QDRANT_COLLECTION

    def _ensure_initialized(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
            if settings.EMBEDDING_QDRANT_URL:
                self._client = QdrantClient(
                    url=settings.EMBEDDING_QDRANT_URL,
                    api_key=settings.EMBEDDING_QDRANT_API_KEY or None,
                )
            else:
                self._client = QdrantClient(":memory:")
            collections = self._client.get_collections().collections
            if not any(c.name == self._collection_name for c in collections):
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )

    def store_embedding(self, vector_id: str, embedding: list[float], metadata: dict) -> str:
        self._ensure_initialized()
        from qdrant_client.http.models import PointStruct
        self._client.upsert(
            collection_name=self._collection_name,
            points=[PointStruct(id=vector_id, vector=embedding, payload=metadata)],
        )
        return vector_id

    def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict[str, Any]]:
        self._ensure_initialized()
        from qdrant_client.http.models import Filter as QdrantFilter
        from qdrant_client.http.models import FieldCondition, MatchValue
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            qdrant_filter = QdrantFilter(must=conditions)
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=qdrant_filter,
        )
        return [
            {"id": r.id, "score": r.score, "metadata": r.payload or {}}
            for r in results
        ]

    def delete(self, vector_id: str) -> bool:
        self._ensure_initialized()
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=[vector_id],
        )
        return True

    def delete_by_session(self, call_session_id: int) -> int:
        self._ensure_initialized()
        from qdrant_client.http.models import Filter as QdrantFilter
        from qdrant_client.http.models import FieldCondition, MatchValue
        result = self._client.delete(
            collection_name=self._collection_name,
            points_selector=QdrantFilter(
                must=[FieldCondition(key="call_session_id", match=MatchValue(value=call_session_id))]
            ),
        )
        return result.status.count if hasattr(result.status, 'count') else 0

    def count(self) -> int:
        self._ensure_initialized()
        result = self._client.count(collection_name=self._collection_name)
        return result.count

    def health_check(self) -> bool:
        try:
            self._ensure_initialized()
            self._client.count(collection_name=self._collection_name)
            return True
        except Exception:
            return False
