from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeviceMetricCreate(BaseModel):
    device_id: int
    battery_level: int | None = None
    charging: bool | None = None
    screen_state: str | None = None
    usb_connected: bool | None = None
    signal_strength: int | None = None
    network_type: str | None = None
    cpu_usage: float | None = None
    memory_usage: float | None = None


class DeviceMetricRead(BaseModel):
    id: int
    device_id: int
    battery_level: int | None
    charging: bool | None
    screen_state: str | None
    usb_connected: bool | None
    signal_strength: int | None
    network_type: str | None
    cpu_usage: float | None
    memory_usage: float | None
    captured_at: datetime

    model_config = {"from_attributes": True}
