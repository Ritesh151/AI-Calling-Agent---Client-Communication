from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCapabilityRead(BaseModel):
    id: int
    device_id: int
    manufacturer: str
    model: str
    android_version: str | None
    supports_auto_answer: bool
    supports_call_detection: bool
    supports_audio_capture: bool
    supports_speaker_recording: bool
    supports_mic_recording: bool
    supports_tts_playback: bool
    supports_background_execution: bool
    capability_score: float | None
    tested_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceProfileRead(BaseModel):
    id: int
    manufacturer: str
    model: str
    android_version: str | None
    profile_name: str
    supported_features: str | None
    known_limitations: str | None
    recommended_strategy: str
    certification_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompatibilityReportRead(BaseModel):
    id: int
    device_id: int
    report_type: str
    score: float | None
    details: str | None
    recommendations: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryLogRead(BaseModel):
    id: int
    device_id: int
    failure_type: str
    recovery_action: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiagnosticsResult(BaseModel):
    device_id: int
    manufacturer: str
    model: str
    android_version: str | None
    adb_status: str
    adb_stability_score: float
    command_success_rate: float
    call_detection_reliable: bool
    recording_reliable: bool
    tts_reliable: bool
    recovery_success_rate: float
    overall_score: float
    certification: str
    recommendations: list[str]
