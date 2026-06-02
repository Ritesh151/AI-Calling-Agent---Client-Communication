from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.audio_processing_job import AudioProcessingJob
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript
from app.repositories.transcript_repository import TranscriptRepository
from app.services.audio_pipeline.audio_pipeline_service import AudioPipelineService
from app.services.transcription.faster_whisper_provider import FasterWhisperProvider

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TranscriptRepository(db)
        self._provider = FasterWhisperProvider()

    def transcribe_recording(self, recording_id: int) -> Transcript:
        recording = self.db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        job = AudioProcessingJob(
            recording_id=recording_id,
            job_type="transcription",
            status="processing",
        )
        self.db.add(job)
        self.db.commit()

        try:
            audio_path = Path(recording.file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Recording file not found: {audio_path}")

            processed_path = AudioPipelineService.preprocess_for_transcription(audio_path)
            transcript_data = self._provider.transcribe(processed_path)

            existing = self.repo.get_by_recording(recording_id)
            if existing:
                existing.transcript_text = transcript_data.transcript_text
                existing.raw_transcript = transcript_data.raw_transcript
                existing.confidence_score = transcript_data.confidence_score
                existing.processing_time = transcript_data.processing_time
                existing.language = transcript_data.language
                existing.word_count = len((transcript_data.transcript_text or "").split())
                transcript = existing
            else:
                transcript = Transcript(
                    recording_id=recording_id,
                    language=transcript_data.language,
                    transcript_text=transcript_data.transcript_text,
                    raw_transcript=transcript_data.raw_transcript,
                    confidence_score=transcript_data.confidence_score,
                    processing_time=transcript_data.processing_time,
                    word_count=len((transcript_data.transcript_text or "").split()),
                )
                self.db.add(transcript)

            recording.recording_status = "transcribed"
            job.status = "completed"
            self.db.commit()
            self.db.refresh(transcript)
            logger.info("Transcription completed for recording %d", recording_id)
            return transcript

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            self.db.commit()
            logger.error("Transcription failed for recording %d: %s", recording_id, e)
            raise

    def get_transcript(self, recording_id: int) -> Transcript | None:
        return self.repo.get_by_recording(recording_id)
