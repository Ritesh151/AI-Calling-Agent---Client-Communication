from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.call_session_repository import CallSessionRepository
from app.repositories.system_log_repository import SystemLogRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.recording_repository import RecordingRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.audio_processing_job_repository import AudioProcessingJobRepository
from app.repositories.greeting_template_repository import GreetingTemplateRepository
from app.repositories.call_summary_repository import CallSummaryRepository
from app.repositories.extracted_entity_repository import ExtractedEntityRepository
from app.repositories.call_classification_repository import CallClassificationRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.ai_processing_job_repository import AIProcessingJobRepository
from app.repositories.device_capability_repository import DeviceCapabilityRepository
from app.repositories.device_profile_repository import DeviceProfileRepository
from app.repositories.compatibility_report_repository import CompatibilityReportRepository
from app.repositories.recovery_log_repository import RecoveryLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "DeviceRepository",
    "CallSessionRepository",
    "SystemLogRepository",
    "SettingRepository",
    "RecordingRepository",
    "TranscriptRepository",
    "AudioProcessingJobRepository",
    "GreetingTemplateRepository",
    "CallSummaryRepository",
    "ExtractedEntityRepository",
    "CallClassificationRepository",
    "EmbeddingRepository",
    "AIProcessingJobRepository",
    "DeviceCapabilityRepository",
    "DeviceProfileRepository",
    "CompatibilityReportRepository",
    "RecoveryLogRepository",
]
