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


class OnePlusHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "oneplus"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        oxygen = await adb_engine.shell(device_id, "getprop ro.oxygen.version")
        has_oxygen = oxygen.status == ADBCommandStatus.SUCCESS and bool(oxygen.stdout.strip())
        if has_oxygen:
            base["supports_auto_answer"] = True
            base["supports_background_execution"] = True
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "input keyevent KEYCODE_CALL")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="oneplus_answer:keyevent_call")
        result = await adb_engine.shell(device_id, "input keyevent 5")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="oneplus_answer:keyevent_5")
        return HandlerResult(success=False, error="OnePlus answer failed", action_taken="oneplus_answer")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="oneplus_record:screenrecord")
        return HandlerResult(success=False, error="OnePlus recording failed", action_taken="oneplus_record")
