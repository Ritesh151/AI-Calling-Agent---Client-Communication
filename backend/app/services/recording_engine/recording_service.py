from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.recording import Recording
from app.repositories.recording_repository import RecordingRepository
from app.services.recording_strategies.strategy_selector import RecordingStrategySelector

logger = logging.getLogger(__name__)


class RecordingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecordingRepository(db)
        self.strategy_selector = RecordingStrategySelector()
        self._active_recordings: dict[int, str] = {}

    async def start_recording(self, call_session_id: int, device_id: str) -> Recording:
        strategy = await self.strategy_selector.select_best_strategy(device_id)
        recording_dir = Path(settings.RECORDING_DIR)
        recording_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"call_{call_session_id}_{timestamp}.{settings.RECORDING_DEFAULT_FORMAT}"
        output_path = recording_dir / filename

        result = await strategy.start_recording(call_session_id, device_id, output_path)
        if not result.success:
            raise RuntimeError(f"Recording failed: {result.error_message}")

        recording = self.repo.create(
            call_session_id=call_session_id,
            filename=filename,
            file_path=str(output_path),
            storage_type=settings.STORAGE_PROVIDER,
            audio_format=settings.RECORDING_DEFAULT_FORMAT,
            recording_status="recording",
        )

        self._active_recordings[call_session_id] = strategy.name
        logger.info("Started recording for call %s using strategy %s", call_session_id, strategy.name)
        return recording

    async def stop_recording(self, call_session_id: int, recording_id: int) -> Recording:
        strategy_name = self._active_recordings.pop(call_session_id, None)
        recording = self.repo.get_by_id(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        if strategy_name:
            strategy = await self.strategy_selector.select_best_strategy("")
            result = await strategy.stop_recording(call_session_id)
            recording.recording_status = "completed" if result.success else "failed"
        else:
            recording.recording_status = "stopped"

        file_path = Path(recording.file_path)
        if file_path.exists():
            recording.file_size = file_path.stat().st_size
            recording.checksum = self._compute_checksum(file_path)

        self.db.commit()
        self.db.refresh(recording)
        return recording

    def get_recording(self, recording_id: int) -> Recording | None:
        return self.repo.get_by_id(recording_id)

    def get_call_recordings(self, call_session_id: int) -> list[Recording]:
        return self.repo.get_by_call_session(call_session_id)

    def _compute_checksum(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def get_strategy_capabilities(self, device_id: str) -> list[dict]:
        results = []
        for strategy in self.strategy_selector.strategies:
            try:
                caps = await strategy.get_capabilities(device_id)
                results.append({"name": strategy.name, "capabilities": caps})
            except Exception as e:
                results.append({"name": strategy.name, "error": str(e)})
        return results
