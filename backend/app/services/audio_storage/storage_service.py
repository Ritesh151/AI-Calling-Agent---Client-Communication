from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.services.audio_storage.local_storage import LocalStorageProvider
from app.services.audio_storage.s3_storage import S3StorageProvider
from app.services.audio_storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class StorageService:
    _providers: dict[str, StorageProvider] = {}

    @classmethod
    def get_provider(cls, name: str | None = None) -> StorageProvider:
        provider_name = name or settings.STORAGE_PROVIDER
        if provider_name not in cls._providers:
            cls._providers[provider_name] = cls._create_provider(provider_name)
        return cls._providers[provider_name]

    @classmethod
    def _create_provider(cls, name: str) -> StorageProvider:
        providers = {
            "local": LocalStorageProvider,
            "s3": S3StorageProvider,
        }
        provider_cls = providers.get(name)
        if not provider_cls:
            logger.warning("Unknown storage provider %s, falling back to local", name)
            provider_cls = LocalStorageProvider
        return provider_cls()

    @classmethod
    async def save(
        cls, source_path: Path, destination: str, provider_name: str | None = None
    ) -> str:
        provider = cls.get_provider(provider_name)
        return await provider.save(source_path, destination)

    @classmethod
    async def load(
        cls, storage_path: str, destination: Path, provider_name: str | None = None
    ) -> Path:
        provider = cls.get_provider(provider_name)
        return await provider.load(storage_path, destination)

    @classmethod
    async def delete(cls, storage_path: str, provider_name: str | None = None) -> bool:
        provider = cls.get_provider(provider_name)
        return await provider.delete(storage_path)

    @classmethod
    async def exists(cls, storage_path: str, provider_name: str | None = None) -> bool:
        provider = cls.get_provider(provider_name)
        return await provider.exists(storage_path)

    @classmethod
    async def get_url(cls, storage_path: str, provider_name: str | None = None) -> str:
        provider = cls.get_provider(provider_name)
        return await provider.get_url(storage_path)
