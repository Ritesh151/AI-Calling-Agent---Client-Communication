from __future__ import annotations

import logging
from pathlib import Path

from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.recording_strategies.base_strategy import (
    BaseRecordingStrategy,
    RecordingResult,
    StrategyCapability,
)

logger = logging.getLogger(__name__)


class ADBRecordingStrategy(BaseRecordingStrategy):
    @property
    def name(self) -> str:
        return "adb_record"

    async def start_recording(self, call_session_id: int, device_id: str, output_path: Path) -> RecordingResult:
        try:
            result = await adb_engine.shell(device_id, f"cmd media recorder start {output_path}")
            if result.status != ADBCommandStatus.SUCCESS:
                return RecordingResult(
                    success=False,
                    error_message=f"ADB recording failed to start: {result.error_message}",
                    strategy_name=self.name,
                )
            return RecordingResult(
                success=True,
                file_path=output_path,
                strategy_name=self.name,
            )
        except Exception as e:
            logger.error("ADB recording strategy failed: %s", e)
            return RecordingResult(
                success=False,
                error_message=str(e),
                strategy_name=self.name,
            )

    async def stop_recording(self, call_session_id: int) -> RecordingResult:
        try:
            result = await adb_engine.shell("", "cmd media recorder stop")
            return RecordingResult(
                success=result.status == ADBCommandStatus.SUCCESS,
                error_message=result.error_message,
                strategy_name=self.name,
            )
        except Exception as e:
            return RecordingResult(
                success=False,
                error_message=str(e),
                strategy_name=self.name,
            )

    async def get_capabilities(self, device_id: str) -> StrategyCapability:
        result = await adb_engine.shell(device_id, "cmd media recorder --help")
        has_media_recorder = result.status == ADBCommandStatus.SUCCESS
        return StrategyCapability(
            can_record_mic=False,
            can_record_speaker=False,
            can_record_call=has_media_recorder,
            supports_parallel=False,
        )

    async def validate_device(self, device_id: str) -> bool:
        result = await adb_engine.shell(device_id, "cmd media recorder --help")
        return result.status == ADBCommandStatus.SUCCESS
