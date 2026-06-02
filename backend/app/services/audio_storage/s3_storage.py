from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.audio_storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    def __init__(self) -> None:
        self._client: Any = None
        self._bucket = settings.STORAGE_S3_BUCKET

    async def _ensure_client(self):
        if self._client is None:
            try:
                import aioboto3
                self._session = aioboto3.Session()
                self._client = await self._session._session.create_client(
                    "s3",
                    endpoint_url=settings.STORAGE_S3_ENDPOINT or None,
                    aws_access_key_id=settings.STORAGE_S3_ACCESS_KEY,
                    aws_secret_access_key=settings.STORAGE_S3_SECRET_KEY,
                    region_name=settings.STORAGE_S3_REGION,
                )
            except ImportError:
                raise RuntimeError("aioboto3 package not installed for S3 storage")

    async def save(self, source_path: Path, destination: str) -> str:
        await self._ensure_client()
        with open(str(source_path), "rb") as f:
            await self._client.put_object(
                Bucket=self._bucket,
                Key=destination,
                Body=f,
            )
        logger.info("Uploaded %s to s3://%s/%s", source_path, self._bucket, destination)
        return f"s3://{self._bucket}/{destination}"

    async def load(self, storage_path: str, destination: Path) -> Path:
        await self._ensure_client()
        key = storage_path.replace(f"s3://{self._bucket}/", "")
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        data = await response["Body"].read()
        with open(str(destination), "wb") as f:
            f.write(data)
        logger.info("Downloaded s3://%s/%s to %s", self._bucket, key, destination)
        return destination

    async def delete(self, storage_path: str) -> bool:
        await self._ensure_client()
        key = storage_path.replace(f"s3://{self._bucket}/", "")
        await self._client.delete_object(Bucket=self._bucket, Key=key)
        logger.info("Deleted s3://%s/%s", self._bucket, key)
        return True

    async def exists(self, storage_path: str) -> bool:
        await self._ensure_client()
        key = storage_path.replace(f"s3://{self._bucket}/", "")
        try:
            await self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
        await self._ensure_client()
        key = storage_path.replace(f"s3://{self._bucket}/", "")
        url = await self._client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
