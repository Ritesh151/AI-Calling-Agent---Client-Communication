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


class SpeakerphoneStrategy(BaseRecordingStrategy):
    @property
    def name(self) -> str:
        return "speakerphone"

    async def start_recording(self, call_session_id: int, device_id: str, output_path: Path) -> RecordingResult:
        try:
            enable_cmd = "content insert --uri content://settings/system --bind name:s:speaker_phone --bind value:i:1"
            result = await adb_engine.shell(device_id, enable_cmd)
            if result.status != ADBCommandStatus.SUCCESS:
                logger.warning("Failed to enable speakerphone: %s", result.error_message)
            result = await adb_engine.shell(device_id, f"screenrecord --source 1 {output_path}")
            if result.status != ADBCommandStatus.SUCCESS:
                return RecordingResult(
                    success=False,
                    error_message=f"Failed to start speakerphone recording: {result.error_message}",
                    strategy_name=self.name,
                )
            return RecordingResult(
                success=True,
                file_path=output_path,
                strategy_name=self.name,
            )
        except Exception as e:
            logger.error("Speakerphone strategy failed: %s", e)
            return RecordingResult(
                success=False,
                error_message=str(e),
                strategy_name=self.name,
            )

    async def stop_recording(self, call_session_id: int) -> RecordingResult:
        try:
            result = await adb_engine.shell("", "pkill -f screenrecord")
            disable_cmd = "content insert --uri content://settings/system --bind name:s:speaker_phone --bind value:i:0"
            await adb_engine.shell("", disable_cmd)
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
            can_record_speaker=True,
            can_record_call=False,
            supports_parallel=False,
        )

    async def validate_device(self, device_id: str) -> bool:
        result = await adb_engine.shell(device_id, "which screenrecord")
        return result.status == ADBCommandStatus.SUCCESS and "screenrecord" in result.stdout
