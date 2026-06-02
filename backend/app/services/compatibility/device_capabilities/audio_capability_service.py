from __future__ import annotations

import logging

from app.services.adb_watcher import ADBCommandStatus, adb_engine

logger = logging.getLogger(__name__)


class AudioCapabilityService:
    async def determine_audio_capabilities(self, device_id: str) -> dict[str, bool | str]:
        results: dict[str, bool | str] = {
            "can_use_microphone": False,
            "can_use_speakerphone": False,
            "can_use_hybrid": False,
            "can_play_tts": False,
            "recommended_strategy": "none",
        }

        scr = await adb_engine.shell(device_id, "which screenrecord")
        has_screenrecord = scr.status == ADBCommandStatus.SUCCESS and "screenrecord" in scr.stdout

        media = await adb_engine.shell(device_id, "cmd media recorder --help")
        has_media_recorder = media.status == ADBCommandStatus.SUCCESS

        audio = await adb_engine.shell(device_id, "dumpsys media.audio_flinger")
        has_audio = audio.status == ADBCommandStatus.SUCCESS

        results["can_use_microphone"] = has_screenrecord
        results["can_use_speakerphone"] = has_screenrecord

        if has_media_recorder:
            results["can_use_hybrid"] = True
            results["recommended_strategy"] = "hybrid"
        elif has_screenrecord:
            results["recommended_strategy"] = "microphone"
        else:
            results["recommended_strategy"] = "none"

        results["can_play_tts"] = has_audio
        results["supports_media_recorder"] = has_media_recorder
        results["supports_screenrecord"] = has_screenrecord

        return results

    async def can_record_long_session(self, device_id: str) -> bool:
        idle = await adb_engine.shell(device_id, "dumpsys deviceidle")
        if idle.status != ADBCommandStatus.SUCCESS:
            return False
        return "mState=ACTIVE" in idle.stdout or "mState=IDLE" in idle.stdout
