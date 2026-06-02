from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorProvider(ABC):
    @abstractmethod
    def store_embedding(self, vector_id: str, embedding: list[float], metadata: dict) -> str:
        ...

    @abstractmethod
    def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def delete(self, vector_id: str) -> bool:
        ...

    @abstractmethod
    def delete_by_session(self, call_session_id: int) -> int:
        ...

    @abstractmethod
    def count(self) -> int:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...
