from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandlerResult:
    success: bool
    data: Any = None
    error: str | None = None
    action_taken: str = ""


class ManufacturerHandler(ABC):
    @property
    @abstractmethod
    def manufacturer_name(self) -> str:
        ...

    @abstractmethod
    async def initialize(self, device_id: str) -> HandlerResult:
        ...

    @abstractmethod
    async def validate_device(self, device_id: str) -> bool:
        ...

    @abstractmethod
    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        ...

    @abstractmethod
    async def detect_call(self, device_id: str) -> HandlerResult:
        ...

    @abstractmethod
    async def answer_call(self, device_id: str) -> HandlerResult:
        ...

    @abstractmethod
    async def play_greeting(self, device_id: str, audio_path: str) -> HandlerResult:
        ...

    @abstractmethod
    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        ...

    @abstractmethod
    async def stop_recording(self, device_id: str) -> HandlerResult:
        ...

    @abstractmethod
    async def recover(self, device_id: str, failure: str) -> HandlerResult:
        ...
