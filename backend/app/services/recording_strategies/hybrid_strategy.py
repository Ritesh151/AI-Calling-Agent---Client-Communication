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


class HybridStrategy(BaseRecordingStrategy):
    @property
    def name(self) -> str:
        return "hybrid"

    async def start_recording(self, call_session_id: int, device_id: str, output_path: Path) -> RecordingResult:
        try:
            result = await adb_engine.shell(device_id, f"cmd media recorder start {output_path}")
            if result.status != ADBCommandStatus.SUCCESS:
                return RecordingResult(
                    success=False,
                    error_message=f"Hybrid recording failed: {result.error_message}",
                    strategy_name=self.name,
                )
            pull_result = await adb_engine.execute(device_id, f"pull {output_path} {output_path}")
            if pull_result.status != ADBCommandStatus.SUCCESS:
                logger.warning("Hybrid pull failed: %s", pull_result.error_message)
            return RecordingResult(
                success=True,
                file_path=output_path,
                strategy_name=self.name,
            )
        except Exception as e:
            logger.error("Hybrid strategy failed: %s", e)
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
        return StrategyCapability(
            can_record_mic=False,
            can_record_speaker=False,
            can_record_call=True,
            supports_parallel=False,
        )

    async def validate_device(self, device_id: str) -> bool:
        result = await adb_engine.shell(device_id, "cmd media recorder --help")
        return result.status == ADBCommandStatus.SUCCESS
