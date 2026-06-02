from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIAnalysisConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 2048
    retry_count: int = 3
    timeout_seconds: int = 30
    local_model_path: str = ""
    api_key: str = ""
    api_base: str = ""


@dataclass
class AIAnalysisResult:
    success: bool
    content: str = ""
    error: str | None = None
    token_usage: dict = field(default_factory=dict)
    model: str = ""


class AIProvider(ABC):
    @abstractmethod
    def analyze(self, prompt: str, system_prompt: str | None = None, max_tokens: int | None = None) -> AIAnalysisResult:
        ...

    @abstractmethod
    def structured_analysis(self, prompt: str, output_format: dict, system_prompt: str | None = None) -> AIAnalysisResult:
        ...

    @abstractmethod
    def validate(self) -> bool:
        ...
