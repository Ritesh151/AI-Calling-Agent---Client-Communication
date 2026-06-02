from __future__ import annotations

import logging
from typing import Any

from app.services.compatibility.manufacturer_handlers.handler_registry import (
    HandlerRegistry,
)

logger = logging.getLogger(__name__)


class StrategyResolver:
    RECORDING_STRATEGIES = {"microphone", "speakerphone", "adb", "hybrid"}

    async def resolve(
        self,
        device_id: str,
        manufacturer: str | None = None,
        capabilities: dict[str, bool] | None = None,
    ) -> str:
        caps = capabilities or await self._detect_capabilities(device_id, manufacturer)
        score_map: list[tuple[str, float]] = []

        score_map.append(("microphone", self._score_microphone(caps)))
        score_map.append(("speakerphone", self._score_speakerphone(caps)))
        score_map.append(("adb", self._score_adb(caps)))
        score_map.append(("hybrid", self._score_hybrid(caps)))

        score_map.sort(key=lambda x: x[1], reverse=True)
        best = score_map[0][0] if score_map[0][1] > 0 else "none"

        logger.info("Strategy resolved for %s: %s (scores: %s)", device_id, best, dict(score_map))
        return best

    async def _detect_capabilities(self, device_id: str, manufacturer: str | None) -> dict[str, bool]:
        handler = HandlerRegistry.resolve_for_device(device_id, manufacturer or "")
        return await handler.detect_capabilities(device_id)

    def _score_microphone(self, caps: dict[str, bool]) -> float:
        score = 0.0
        if caps.get("supports_audio_capture"):
            score += 30
        if caps.get("supports_mic_recording"):
            score += 40
        if caps.get("supports_speaker_recording"):
            score += 10
        return score

    def _score_speakerphone(self, caps: dict[str, bool]) -> float:
        score = 0.0
        if caps.get("supports_audio_capture"):
            score += 20
        if caps.get("supports_speaker_recording"):
            score += 50
        return score

    def _score_adb(self, caps: dict[str, bool]) -> float:
        score = 0.0
        if caps.get("supports_auto_answer"):
            score += 30
        if caps.get("supports_background_execution"):
            score += 30
        return score

    def _score_hybrid(self, caps: dict[str, bool]) -> float:
        score = 0.0
        if caps.get("supports_audio_capture"):
            score += 20
        if caps.get("supports_mic_recording"):
            score += 20
        if caps.get("supports_speaker_recording"):
            score += 20
        if caps.get("supports_auto_answer"):
            score += 10
        if caps.get("supports_background_execution"):
            score += 10
        return score
