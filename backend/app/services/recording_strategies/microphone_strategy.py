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


class MicrophoneStrategy(BaseRecordingStrategy):
    @property
    def name(self) -> str:
        return "microphone"

    async def start_recording(self, call_session_id: int, device_id: str, output_path: Path) -> RecordingResult:
        try:
            result = await adb_engine.shell(device_id, "dumpsys media.audio_flinger")
            if result.status != ADBCommandStatus.SUCCESS:
                return RecordingResult(
                    success=False,
                    error_message=f"Failed to access audio flinger: {result.error_message}",
                    strategy_name=self.name,
                )
            result = await adb_engine.shell(device_id, f"screenrecord --time-limit 0 {output_path}")
            if result.status != ADBCommandStatus.SUCCESS:
                return RecordingResult(
                    success=False,
                    error_message=f"Failed to start recording: {result.error_message}",
                    strategy_name=self.name,
                )
            return RecordingResult(
                success=True,
                file_path=output_path,
                strategy_name=self.name,
            )
        except Exception as e:
            logger.error("Microphone strategy failed: %s", e)
            return RecordingResult(
                success=False,
                error_message=str(e),
                strategy_name=self.name,
            )

    async def stop_recording(self, call_session_id: int) -> RecordingResult:
        try:
            result = await adb_engine.shell("", "pkill -f screenrecord")
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
        return StrategyCapability(
            can_record_mic=True,
            can_record_speaker=False,
            can_record_call=False,
            supports_parallel=False,
        )

    async def validate_device(self, device_id: str) -> bool:
        result = await adb_engine.shell(device_id, "which screenrecord")
        return result.status == ADBCommandStatus.SUCCESS and "screenrecord" in result.stdout
