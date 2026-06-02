from __future__ import annotations

import re
from typing import Any

from app.core.config import settings


class ChunkingService:
    def __init__(self, chunk_size: int | None = None, overlap: int | None = None) -> None:
        self.chunk_size = chunk_size or settings.EMBEDDING_CHUNK_SIZE
        self.overlap = overlap or settings.EMBEDDING_CHUNK_OVERLAP

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[dict[str, Any]]:
        if not text:
            return []
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk: list[str] = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_meta = dict(metadata or {})
                chunk_meta["chunk_index"] = chunk_index
                chunks.append({"text": chunk_text, "metadata": chunk_meta})
                chunk_index += 1
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text.copy()
                current_length = sum(len(s) for s in current_chunk)
            current_chunk.append(sentence)
            current_length += sentence_len

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_meta = dict(metadata or {})
            chunk_meta["chunk_index"] = chunk_index
            chunks.append({"text": chunk_text, "metadata": chunk_meta})

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        text = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap(self, sentences: list[str]) -> list[str]:
        overlap_chars = 0
        overlap_sentences: list[str] = []
        for s in reversed(sentences):
            if overlap_chars >= self.overlap:
                break
            overlap_sentences.insert(0, s)
            overlap_chars += len(s)
        return overlap_sentences
