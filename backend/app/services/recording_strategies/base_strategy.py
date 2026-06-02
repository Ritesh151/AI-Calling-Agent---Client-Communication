from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RecordingResult:
    success: bool
    file_path: Path | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    strategy_name: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class StrategyCapability:
    can_record_mic: bool = False
    can_record_speaker: bool = False
    can_record_call: bool = False
    supports_parallel: bool = False


class BaseRecordingStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def start_recording(self, call_session_id: int, device_id: str, output_path: Path) -> RecordingResult:
        ...

    @abstractmethod
    async def stop_recording(self, call_session_id: int) -> RecordingResult:
        ...

    @abstractmethod
    async def get_capabilities(self, device_id: str) -> StrategyCapability:
        ...

    @abstractmethod
    async def validate_device(self, device_id: str) -> bool:
        ...
