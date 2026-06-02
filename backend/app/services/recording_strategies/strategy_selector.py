from __future__ import annotations

import logging

from app.services.recording_strategies.adb_strategy import ADBRecordingStrategy
from app.services.recording_strategies.base_strategy import (
    BaseRecordingStrategy,
    StrategyCapability,
)
from app.services.recording_strategies.hybrid_strategy import HybridStrategy
from app.services.recording_strategies.microphone_strategy import MicrophoneStrategy
from app.services.recording_strategies.speakerphone_strategy import SpeakerphoneStrategy

logger = logging.getLogger(__name__)


class RecordingStrategySelector:
    def __init__(self) -> None:
        self.strategies: list[BaseRecordingStrategy] = [
            ADBRecordingStrategy(),
            HybridStrategy(),
            SpeakerphoneStrategy(),
            MicrophoneStrategy(),
        ]

    async def select_best_strategy(self, device_id: str) -> BaseRecordingStrategy:
        best_index = -1
        best_capability_score = -1

        for i, strategy in enumerate(self.strategies):
            try:
                is_valid = await strategy.validate_device(device_id)
                if not is_valid:
                    logger.debug("Strategy %s not available on device %s", strategy.name, device_id)
                    continue

                capabilities = await strategy.get_capabilities(device_id)
                score = self._score_capabilities(capabilities)
                if score > best_capability_score:
                    best_capability_score = score
                    best_index = i
            except Exception as e:
                logger.warning("Error checking strategy %s: %s", strategy.name, e)
                continue

        if best_index == -1:
            logger.warning("No strategy available, defaulting to microphone")
            return MicrophoneStrategy()

        logger.info(
            "Selected recording strategy %s with score %d",
            self.strategies[best_index].name,
            best_capability_score,
        )
        return self.strategies[best_index]

    def _score_capabilities(self, caps: StrategyCapability) -> int:
        score = 0
        if caps.can_record_call:
            score += 100
        if caps.can_record_speaker:
            score += 50
        if caps.can_record_mic:
            score += 25
        if caps.supports_parallel:
            score += 10
        return score
