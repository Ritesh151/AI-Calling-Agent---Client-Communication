#!/usr/bin/env python3
"""Seed default system settings into the database."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import Base, SessionLocal, engine
from app.db.models.setting import Setting

DEFAULT_SETTINGS = [
    # General
    (
        "owner_name",
        "AI Calling System, Made by Ritesh Gajjar",
        "Owner/company name for greetings",
        "general",
    ),
    ("default_language", "en-US", "Default system language", "general"),
    # Greeting
    (
        "greeting_message",
        "Hello, you have reached AI Call Reception. Please leave a message after the tone.",
        "Call greeting message",
        "greeting",
    ),
    ("greeting_enabled", "true", "Enable/disable greeting playback", "greeting"),
    # Recording
    ("recording_enabled", "true", "Enable/disable call recording", "recording"),
    ("recording_format", "wav", "Recording audio format (wav, mp3, ogg)", "recording"),
    (
        "max_recording_duration",
        "300",
        "Maximum recording duration in seconds",
        "recording",
    ),
    # Transcription
    ("transcription_enabled", "true", "Enable/disable transcription", "transcription"),
    ("transcription_language", "en-US", "Transcription language code", "transcription"),
    # Device
    ("device_timeout", "10", "Device command timeout in seconds", "device"),
    (
        "heartbeat_interval",
        "30",
        "Device heartbeat check interval in seconds",
        "device",
    ),
    # System
    ("tts_enabled", "false", "Enable text-to-speech for greetings", "system"),
    ("log_level", "INFO", "Application log level", "system"),
    ("max_call_duration", "600", "Maximum call duration in seconds", "system"),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for key, value, description, category in DEFAULT_SETTINGS:
            existing = db.query(Setting).filter(Setting.key == key).first()
            if existing:
                existing.value = value
                existing.description = description
                existing.category = category
            else:
                setting = Setting(
                    key=key,
                    value=value,
                    description=description,
                    category=category,
                )
                db.add(setting)
        db.commit()
        print(f"Seeded {len(DEFAULT_SETTINGS)} default settings.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding settings: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
