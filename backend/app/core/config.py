from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "AI Call Reception System"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Production-grade AI-powered call reception system"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: str | bool) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "on", "debug", "development")
        return False

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_WORKERS: int = 4
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "callreception"
    POSTGRES_PASSWORD: str = "callreception_secret"
    POSTGRES_DB: str = "callreception"
    DATABASE_URL: PostgresDsn | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str) and v:
            return v
        return str(
            MultiHostUrl.build(
                scheme="postgresql+psycopg2",
                username=values.data.get("POSTGRES_USER", "callreception"),
                password=values.data.get("POSTGRES_PASSWORD", "callreception_secret"),
                host=values.data.get("POSTGRES_HOST", "postgres"),
                port=values.data.get("POSTGRES_PORT", 5432),
                path=values.data.get("POSTGRES_DB", "callreception"),
            )
        )

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: RedisDsn | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str) and v:
            return v
        password = values.data.get("REDIS_PASSWORD", "")
        auth_part = f":{password}@" if password else ""
        return f"redis://{auth_part}{values.data.get('REDIS_HOST', 'redis')}:{values.data.get('REDIS_PORT', 6379)}/{values.data.get('REDIS_DB', 0)}"

    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_64"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BCRYPT_ROUNDS: int = 12

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 300

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_MAX_BYTES: int = 10485760
    LOG_FILE_BACKUP_COUNT: int = 5

    SENTRY_DSN: str | None = None

    ADB_HOST: str = "127.0.0.1"
    ADB_PORT: int = 5037
    ADB_MAX_RETRIES: int = 3
    ADB_RETRY_DELAY_SECONDS: float = 1.0
    ADB_COMMAND_QUEUE_MAX_SIZE: int = 100
    DEVICE_HEARTBEAT_INTERVAL_SECONDS: int = 5
    DEVICE_TIMEOUT_SECONDS: int = 10
    DEVICE_WATCH_INTERVAL_SECONDS: int = 5
    CALL_POLL_INTERVAL_SECONDS: float = 1.0
    AUTO_ANSWER_ENABLED: bool = True
    AUTO_ANSWER_DELAY_SECONDS: float = 2.0
    AUTO_ANSWER_RETRY_COUNT: int = 3
    EVENT_BUS_MAX_SUBSCRIBERS: int = 50
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "ai_call_reception"
    MONGODB_ENABLED: bool = True

    TTS_DEFAULT_PROVIDER: str = "edge"
    TTS_OPENAI_API_KEY: str = ""
    TTS_OPENAI_MODEL: str = "tts-1"
    TTS_OPENAI_VOICE: str = "alloy"
    TTS_CACHE_ENABLED: bool = True
    TTS_CACHE_DIR: str = "data/tts_cache"
    TTS_DEFAULT_LANGUAGE: str = "en-US"
    TTS_DEFAULT_VOICE: str = "en-US-JennyNeural"

    RECORDING_DIR: str = "data/recordings"
    RECORDING_DEFAULT_FORMAT: str = "wav"
    RECORDING_SAMPLE_RATE: int = 16000
    RECORDING_CHANNELS: int = 1
    RECORDING_MAX_DURATION_SECONDS: int = 300
    RECORDING_BEEP_FILE: str = "data/beep.wav"

    STORAGE_PROVIDER: str = "local"
    STORAGE_S3_ENDPOINT: str = ""
    STORAGE_S3_ACCESS_KEY: str = ""
    STORAGE_S3_SECRET_KEY: str = ""
    STORAGE_S3_BUCKET: str = ""
    STORAGE_S3_REGION: str = "us-east-1"

    TRANSCRIPTION_PROVIDER: str = "faster_whisper"
    TRANSCRIPTION_MODEL_SIZE: str = "base"
    TRANSCRIPTION_DEVICE: str = "cpu"
    TRANSCRIPTION_COMPUTE_TYPE: str = "int8"
    TRANSCRIPTION_LANGUAGE: str = "en"
    TRANSCRIPTION_BEAM_SIZE: int = 5

    RETENTION_RECORDING_DAYS: int = 90
    RETENTION_ARCHIVE_ENABLED: bool = False
    RETENTION_AUTO_CLEANUP: bool = True
    RETENTION_CLEANUP_INTERVAL_HOURS: int = 24

    AI_ANALYSIS_PROVIDER: str = "openai"
    AI_ANALYSIS_API_KEY: str = ""
    AI_ANALYSIS_API_BASE: str = ""
    AI_ANALYSIS_MODEL: str = "gpt-4o-mini"
    AI_ANALYSIS_LOCAL_MODEL: str = "llama3"
    AI_ANALYSIS_TEMPERATURE: float = 0.1
    AI_ANALYSIS_MAX_TOKENS: int = 2048
    AI_ANALYSIS_RETRY_COUNT: int = 3

    EMBEDDING_PROVIDER: str = "chromadb"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_CHUNK_SIZE: int = 512
    EMBEDDING_CHUNK_OVERLAP: int = 64
    EMBEDDING_CHROMA_PATH: str = "data/chromadb"
    EMBEDDING_QDRANT_URL: str = ""
    EMBEDDING_QDRANT_API_KEY: str = ""
    EMBEDDING_QDRANT_COLLECTION: str = "call_embeddings"
    EMBEDDING_OPENAI_API_KEY: str = ""
    EMBEDDING_OPENAI_MODEL: str = "text-embedding-3-small"

    SEARCH_DEFAULT_LIMIT: int = 20
    SEARCH_MAX_LIMIT: int = 100
    SEARCH_MIN_SCORE: float = 0.3

    INSIGHT_SCHEDULE_HOURS: int = 24
    REPORT_DIR: str = "data/reports"

    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent


settings = Settings()
