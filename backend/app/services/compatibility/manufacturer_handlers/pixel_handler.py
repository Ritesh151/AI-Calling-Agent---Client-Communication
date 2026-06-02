from __future__ import annotations

import logging

from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.compatibility.manufacturer_handlers.generic_handler import (
    GenericAndroidHandler,
)
from app.services.compatibility.manufacturer_handlers.manufacturer_handler import (
    HandlerResult,
)

logger = logging.getLogger(__name__)


class PixelHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "pixel"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        base["supports_auto_answer"] = True
        base["supports_call_detection"] = True
        base["supports_background_execution"] = True
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "input keyevent KEYCODE_CALL")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="pixel_answer:keyevent_call")
        return HandlerResult(success=False, error="Pixel answer failed", action_taken="pixel_answer")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="pixel_record:screenrecord")
        return HandlerResult(success=False, error="Pixel recording failed", action_taken="pixel_record")

    async def play_greeting(self, device_id: str, audio_path: str) -> HandlerResult:
        cmd = f"mediaplayer {audio_path}"
        result = await adb_engine.shell(device_id, cmd)
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="pixel_play:mediaplayer")
        return await super().play_greeting(device_id, audio_path)
