from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try to import pydub, but make it optional for Python 3.13+ compatibility
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    logger.warning("pydub not available - audio conversion features disabled")
    PYDUB_AVAILABLE = False


class AudioPipelineService:
    @staticmethod
    def convert_format(input_path: Path, output_format: str = "wav") -> Path:
        if not PYDUB_AVAILABLE:
            logger.error("pydub not available - cannot convert audio format")
            raise RuntimeError("Audio pipeline service not available. Install pydub: pip install pydub")
        
        output_path = input_path.with_suffix(f".{output_format}")
        audio = AudioSegment.from_file(str(input_path))
        audio.export(str(output_path), format=output_format)
        logger.info("Converted %s to %s", input_path, output_path)
        return output_path

    @staticmethod
    def resample(input_path: Path, sample_rate: int | None = None) -> Path:
        if not PYDUB_AVAILABLE:
            logger.error("pydub not available - cannot resample audio")
            raise RuntimeError("Audio pipeline service not available. Install pydub: pip install pydub")
        
        target_rate = sample_rate or settings.RECORDING_SAMPLE_RATE
        audio = AudioSegment.from_file(str(input_path))
        resampled = audio.set_frame_rate(target_rate)
        output_path = input_path.parent / f"{input_path.stem}_resampled{input_path.suffix}"
        resampled.export(str(output_path), format=input_path.suffix.lstrip("."))
        logger.info("Resampled %s to %d Hz", input_path, target_rate)
        return output_path

    @staticmethod
    def convert_to_mono(input_path: Path) -> Path:
        audio = AudioSegment.from_file(str(input_path))
        if audio.channels > 1:
            mono = audio.set_channels(1)
            output_path = input_path.parent / f"{input_path.stem}_mono{input_path.suffix}"
            mono.export(str(output_path), format=input_path.suffix.lstrip("."))
            logger.info("Converted %s to mono", input_path)
            return output_path
        return input_path

    @staticmethod
    def normalize_volume(input_path: Path, target_dbfs: float = -20.0) -> Path:
        audio = AudioSegment.from_file(str(input_path))
        change_in_dbfs = target_dbfs - audio.dBFS
        normalized = audio.apply_gain(change_in_dbfs)
        output_path = input_path.parent / f"{input_path.stem}_normalized{input_path.suffix}"
        normalized.export(str(output_path), format=input_path.suffix.lstrip("."))
        logger.info("Normalized %s to %.1f dBFS", input_path, target_dbfs)
        return output_path

    @staticmethod
    def trim_silence(input_path: Path, silence_thresh: int = -40, min_silence_len: int = 500) -> Path:
        audio = AudioSegment.from_file(str(input_path))
        trimmed = audio.strip_silence(silence_thresh=silence_thresh, padding=100)
        output_path = input_path.parent / f"{input_path.stem}_trimmed{input_path.suffix}"
        trimmed.export(str(output_path), format=input_path.suffix.lstrip("."))
        logger.info("Trimmed silence from %s", input_path)
        return output_path

    @staticmethod
    def add_beep(input_path: Path, beep_path: Path | None = None) -> Path:
        beep_path = beep_path or Path(settings.RECORDING_BEEP_FILE)
        if not beep_path.exists():
            logger.warning("Beep file not found at %s, skipping", beep_path)
            return input_path
        audio = AudioSegment.from_file(str(input_path))
        beep = AudioSegment.from_file(str(beep_path))
        padded = AudioSegment.silent(duration=1000) + beep + audio
        output_path = input_path.parent / f"{input_path.stem}_with_beep{input_path.suffix}"
        padded.export(str(output_path), format=input_path.suffix.lstrip("."))
        logger.info("Added beep to %s", input_path)
        return output_path

    @staticmethod
    def get_duration(input_path: Path) -> float:
        audio = AudioSegment.from_file(str(input_path))
        return len(audio) / 1000.0

    @staticmethod
    def preprocess_for_transcription(input_path: Path) -> Path:
        current = input_path
        current = AudioPipelineService.convert_to_mono(current)
        current = AudioPipelineService.resample(current)
        current = AudioPipelineService.normalize_volume(current)
        logger.info("Preprocessed %s for transcription -> %s", input_path, current)
        return current
