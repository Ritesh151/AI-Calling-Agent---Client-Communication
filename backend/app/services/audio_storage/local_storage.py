from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.core.config import settings
from app.services.audio_storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self._base_path = Path(settings.RECORDING_DIR)

    async def save(self, source_path: Path, destination: str) -> str:
        dest_path = self._base_path / destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source_path), str(dest_path))
        logger.info("Saved recording to %s", dest_path)
        return str(dest_path)

    async def load(self, storage_path: str, destination: Path) -> Path:
        src = self._resolve_path(storage_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(destination))
        logger.info("Loaded recording from %s to %s", src, destination)
        return destination

    async def delete(self, storage_path: str) -> bool:
        path = self._resolve_path(storage_path)
        if path.exists():
            path.unlink()
            logger.info("Deleted recording %s", path)
            return True
        logger.warning("Recording not found for deletion: %s", path)
        return False

    async def exists(self, storage_path: str) -> bool:
        return self._resolve_path(storage_path).exists()

    async def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
        return f"file://{self._resolve_path(storage_path)}"

    def _resolve_path(self, storage_path: str) -> Path:
        p = Path(storage_path)
        if p.is_absolute():
            return p
        return self._base_path / p
