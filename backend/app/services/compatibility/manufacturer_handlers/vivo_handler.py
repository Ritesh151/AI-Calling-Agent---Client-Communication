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


class VivoHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "vivo"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        funtouch = await adb_engine.shell(device_id, "getprop ro.vivo.os.build.display.id")
        has_funtouch = funtouch.status == ADBCommandStatus.SUCCESS and bool(funtouch.stdout.strip())
        if has_funtouch:
            base["supports_background_execution"] = False
            base["supports_auto_answer"] = False
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        commands = ["input keyevent KEYCODE_CALL", "input keyevent 5", "input tap 500 500"]
        for cmd in commands:
            result = await adb_engine.shell(device_id, cmd)
            if result.status == ADBCommandStatus.SUCCESS:
                return HandlerResult(success=True, action_taken=f"vivo_answer:{cmd[:30]}")
        return HandlerResult(success=False, error="Vivo answer failed", action_taken="vivo_answer")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="vivo_record:screenrecord")
        return HandlerResult(success=False, error="Vivo recording failed", action_taken="vivo_record")
