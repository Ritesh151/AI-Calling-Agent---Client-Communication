from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=255)
    android_id: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    android_version: str | None = None


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(default=None, min_length=1, max_length=255)
    android_id: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    android_version: str | None = None
    status: str | None = Field(
        default=None, pattern=r"^(connected|disconnected|error|busy)$"
    )
    is_connected: bool | None = None
    battery_level: int | None = None
    charging: bool | None = None
    screen_state: str | None = None
    connection_type: str | None = None
    usb_debugging_enabled: bool | None = None
    adb_status: str | None = None
    device_ip: str | None = None


class DeviceRead(BaseModel):
    id: int
    user_id: int | None
    device_name: str
    android_id: str | None
    serial_number: str | None
    manufacturer: str | None
    model: str | None
    android_version: str | None
    status: str
    is_connected: bool
    connection_type: str | None
    usb_debugging_enabled: bool | None
    adb_status: str | None
    battery_level: int | None
    charging: bool | None
    screen_state: str | None
    device_ip: str | None
    last_seen: datetime | None
    heartbeat_at: datetime | None
    last_command_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
