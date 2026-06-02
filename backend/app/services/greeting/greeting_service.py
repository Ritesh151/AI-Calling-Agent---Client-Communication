from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.greeting_template_repository import GreetingTemplateRepository
from app.services.tts_engine.tts_service import TTSFactory

logger = logging.getLogger(__name__)


class GreetingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GreetingTemplateRepository(db)

    def get_greeting_text(self, device_id: int | None = None, language: str | None = None) -> str:
        lang = language or settings.TTS_DEFAULT_LANGUAGE
        template = self.repo.get_default(language=lang)
        if template is None:
            templates = self.repo.get_by_language(lang)
            template = templates[0] if templates else None
        if template is None:
            template = self.repo.get_default()
        if template is None:
            return self._default_greeting()
        return template.template_text

    async def generate_greeting_audio(self, device_id: int | None = None, language: str | None = None) -> Path:
        text = self.get_greeting_text(device_id, language)
        return await TTSFactory.generate_speech(text, language=language)

    def _default_greeting(self) -> str:
        return "Hello, you have reached an automated assistant. Please hold while I connect you."
