from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    @abstractmethod
    async def save(self, source_path: Path, destination: str) -> str:
        ...

    @abstractmethod
    async def load(self, storage_path: str, destination: Path) -> Path:
        ...

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        ...

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        ...

    @abstractmethod
    async def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
        ...
