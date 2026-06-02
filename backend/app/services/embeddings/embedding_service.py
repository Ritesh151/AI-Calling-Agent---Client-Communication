from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.embedding_model import EmbeddingRecord
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.embeddings.chromadb_provider import ChromaDBProvider
from app.services.embeddings.chunking_service import ChunkingService
from app.services.embeddings.qdrant_provider import QdrantProvider
from app.services.embeddings.vector_provider import VectorProvider
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EmbeddingRepository(db)
        self.chunking = ChunkingService()
        self._vector_provider: VectorProvider | None = None
        self._embedding_model: Any = None

    @property
    def vector_provider(self) -> VectorProvider:
        if self._vector_provider is None:
            provider_name = settings.EMBEDDING_PROVIDER
            if provider_name == "qdrant":
                self._vector_provider = QdrantProvider()
            else:
                self._vector_provider = ChromaDBProvider()
        return self._vector_provider

    def generate_embeddings(self, call_session_id: int, text: str) -> list[dict[str, Any]]:
        chunks = self.chunking.chunk_text(text, {"call_session_id": call_session_id})
        if not chunks:
            return []
        results = []
        for chunk in chunks:
            embedding = self._compute_embedding(chunk["text"])
            vector_id = str(uuid.uuid4())
            metadata = chunk["metadata"]
            metadata["text"] = chunk["text"]
            metadata["call_session_id"] = call_session_id
            self.vector_provider.store_embedding(vector_id, embedding, metadata)
            record = self.repo.create(
                call_session_id=call_session_id,
                embedding_provider=settings.EMBEDDING_PROVIDER,
                embedding_model=settings.EMBEDDING_MODEL,
                vector_id=vector_id,
                chunk_text=chunk["text"],
                chunk_index=metadata.get("chunk_index"),
            )
            results.append({"vector_id": vector_id, "chunk_index": metadata.get("chunk_index")})

        event_bus.publish_nowait(Event(
            type="embedding_created",
            data={"call_session_id": call_session_id, "chunks": len(chunks)},
            priority=EventPriority.NORMAL,
        ))
        logger.info("Generated %d embeddings for call %d", len(chunks), call_session_id)
        return results

    def search(self, query: str, limit: int = 10, filters: dict | None = None) -> list[dict[str, Any]]:
        query_embedding = self._compute_embedding(query)
        results = self.vector_provider.search(query_embedding, limit=limit, filters=filters)
        for r in results:
            meta = r.get("metadata", {})
            r["call_session_id"] = meta.get("call_session_id")
            r["chunk_text"] = meta.get("text", "")
        return results

    def delete_session_embeddings(self, call_session_id: int) -> int:
        count = self.vector_provider.delete_by_session(call_session_id)
        self.repo.delete_by_session(call_session_id)
        return count

    def _compute_embedding(self, text: str) -> list[float]:
        try:
            if settings.EMBEDDING_PROVIDER == "openai":
                return self._openai_embedding(text)
            return self._local_embedding(text)
        except Exception as e:
            logger.error("Embedding computation failed, falling back to local: %s", e)
            return self._local_embedding(text)

    def _local_embedding(self, text: str) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer
            if self._embedding_model is None:
                self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            result = self._embedding_model.encode(text)
            return result.tolist()
        except ImportError:
            logger.warning("sentence-transformers not installed, using random embedding")
            import random
            return [random.uniform(-1, 1) for _ in range(settings.EMBEDDING_DIMENSION)]

    def _openai_embedding(self, text: str) -> list[float]:
        import openai
        client = openai.OpenAI(api_key=settings.EMBEDDING_OPENAI_API_KEY)
        response = client.embeddings.create(
            model=settings.EMBEDDING_OPENAI_MODEL,
            input=text,
        )
        return response.data[0].embedding
