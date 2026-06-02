"""
Fixed Greeting Engine - Deterministic, script-based greetings
No AI generation, no dynamic variations
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation, ConversationMessage
from app.db.models.call_session import CallSession
from app.core.exceptions import NotFoundException
from app.services.tts_engine.tts_service import TTSFactory
from app.services.event_bus import event_bus, Event, EventPriority

logger = logging.getLogger(__name__)


class GreetingPhase(Enum):
    """Greeting conversation phases"""
    LANGUAGE_SELECTION = "language_selection"
    LANGUAGE_CONFIRMED = "language_confirmed"
    READY_FOR_QUESTIONS = "ready_for_questions"


class Language(Enum):
    """Supported languages"""
    ENGLISH = "english"
    HINDI = "hindi"
    GUJARATI = "gujarati"


# Fixed greeting scripts - No changes, no variations
GREETINGS = {
    Language.ENGLISH: {
        "initial": "Hello, I am from RG Opti Matrix Solutions.\nWhich language would you prefer for communication?\nPress or say:\n1 for English\n2 for Hindi\n3 for Gujarati",
        "confirmation": "Thank you.\nI will now ask you a few questions regarding your project requirements.\nPlease answer each question carefully.",
        "language_name": "English"
    },
    Language.HINDI: {
        "initial": "नमस्ते, मैं RG Opti Matrix Solutions से बोल रहा हूँ।\nआप किस भाषा में बात करना पसंद करेंगे?\n1 दबाइए English के लिए\n2 दबाइए हिंदी के लिए\n3 दबाइए ગુજરાતી के लिए",
        "confirmation": "धन्यवाद।\nमैं अब आपकी परियोजना आवश्यकताओं के बारे में कुछ प्रश्न पूछूंगा।\nकृपया प्रत्येक प्रश्न का उत्तर ध्यानपूर्वक दें।",
        "language_name": "हिंदी"
    },
    Language.GUJARATI: {
        "initial": "નમસ્તે, હું RG Opti Matrix Solutions માંથી બોલું છું.\nતમે કઈ ભાષામાં વાતચીત કરવા માંગો છો?\n1 English માટે\n2 Hindi માટે\n3 ગુજરાતી માટે",
        "confirmation": "આભાર.\nહવે હું તમારા પ્રોજેક્ટ વિશે થોડા પ્રશ્નો પૂછીશ.\nકૃપા કરીને દરેક પ્રશ્નનો જવાબ આપો.",
        "language_name": "ગુજરાતી"
    }
}

LANGUAGE_MAP = {
    "1": Language.ENGLISH,
    "english": Language.ENGLISH,
    "en": Language.ENGLISH,
    "2": Language.HINDI,
    "hindi": Language.HINDI,
    "hi": Language.HINDI,
    "3": Language.GUJARATI,
    "gujarati": Language.GUJARATI,
    "gu": Language.GUJARATI,
}


class GreetingEngine:
    """
    Manages fixed greeting flow:
    1. Play language selection greeting
    2. Listen for language choice (1/2/3 or spoken)
    3. Store language selection
    4. Play confirmation greeting in selected language
    5. Ready for question engine
    """
    
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cache_dir = Path("tts_cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def play_initial_greeting(
        self, 
        call_session_id: int,
        device_id: int,
        serial: str
    ) -> dict:
        """
        Play the initial multi-language greeting
        Returns: {status, greeting_audio_path, call_id}
        """
        call = self._get_call(call_session_id)
        conversation = self._ensure_conversation(call_session_id)
        
        # Generate initial greeting audio (English - first language option)
        initial_greeting_text = GREETINGS[Language.ENGLISH]["initial"]
        greeting_audio_path = await TTSFactory.generate_speech(
            text=initial_greeting_text,
            language="english",
            voice="en-US-AriaNeural"  # Professional, neutral voice
        )
        
        # Log greeting started
        self._add_greeting_message(
            conversation,
            phase=GreetingPhase.LANGUAGE_SELECTION,
            content=initial_greeting_text,
            status="played"
        )
        
        logger.info(
            "Initial greeting played: call_id=%s, device_id=%s, audio=%s",
            call_session_id,
            device_id,
            greeting_audio_path
        )
        
        return {
            "status": "greeting_played",
            "call_id": call_session_id,
            "device_id": device_id,
            "audio_path": str(greeting_audio_path),
            "phase": GreetingPhase.LANGUAGE_SELECTION.value,
            "timestamp": datetime.now(UTC).isoformat()
        }

    async def process_language_selection(
        self,
        call_session_id: int,
        language_input: str
    ) -> dict:
        """
        Process language selection (1/2/3 or spoken language name)
        Returns: {status, language, confirmation_audio_path}
        """
        call = self._get_call(call_session_id)
        conversation = self._get_conversation(call_session_id)
        
        if not conversation:
            raise NotFoundException("Conversation not found for this call")
        
        # Normalize language input
        normalized_input = language_input.strip().lower()
        language = self._normalize_language(normalized_input)
        
        if not language:
            logger.warning(
                "Invalid language selection: call_id=%s, input=%s",
                call_session_id,
                language_input
            )
            return {
                "status": "invalid_selection",
                "call_id": call_session_id,
                "input": language_input,
                "reason": "Language not recognized. Please say or press 1, 2, or 3."
            }
        
        # Store language selection in database
        call.language = language.value
        conversation.language = language.value
        conversation.status = GreetingPhase.LANGUAGE_CONFIRMED.value
        
        # Add language selection message
        self._add_greeting_message(
            conversation,
            phase=GreetingPhase.LANGUAGE_CONFIRMED,
            content=f"Language selected: {language.value}",
            status="confirmed",
            language=language.value
        )
        
        # Generate confirmation greeting in selected language
        confirmation_text = GREETINGS[language]["confirmation"]
        confirmation_audio_path = await TTSFactory.generate_speech(
            text=confirmation_text,
            language=language.value,
        )
        
        # Add confirmation message
        self._add_greeting_message(
            conversation,
            phase=GreetingPhase.READY_FOR_QUESTIONS,
            content=confirmation_text,
            status="playing",
            language=language.value
        )
        
        self.db.commit()
        
        logger.info(
            "Language selected: call_id=%s, language=%s, audio=%s",
            call_session_id,
            language.value,
            confirmation_audio_path
        )
        
        return {
            "status": "language_confirmed",
            "call_id": call_session_id,
            "language": language.value,
            "language_display": GREETINGS[language]["language_name"],
            "audio_path": str(confirmation_audio_path),
            "phase": GreetingPhase.READY_FOR_QUESTIONS.value,
            "timestamp": datetime.now(UTC).isoformat()
        }

    async def complete_greeting(
        self,
        call_session_id: int
    ) -> dict:
        """
        Mark greeting as completed and ready for question engine
        """
        conversation = self._get_conversation(call_session_id)
        if not conversation:
            raise NotFoundException("Conversation not found for this call")
        
        conversation.status = "in_progress"
        
        # Add completion message
        self._add_greeting_message(
            conversation,
            phase=GreetingPhase.READY_FOR_QUESTIONS,
            content="Greeting completed. Ready for question engine.",
            status="completed"
        )
        
        self.db.commit()
        
        logger.info(
            "Greeting completed: call_id=%s, language=%s",
            call_session_id,
            conversation.language
        )
        
        # Publish event for question engine to start
        await event_bus.publish(
            Event(
                type="greeting_completed",
                priority=EventPriority.HIGH,
                data={
                    "call_session_id": call_session_id,
                    "language": conversation.language,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
        )
        
        return {
            "status": "greeting_completed",
            "call_id": call_session_id,
            "language": conversation.language,
            "next_phase": "question_engine",
            "timestamp": datetime.now(UTC).isoformat()
        }

    def get_greeting_status(self, call_session_id: int) -> dict:
        """Get current greeting status for a call"""
        conversation = self._get_conversation(call_session_id)
        if not conversation:
            raise NotFoundException("Conversation not found for this call")
        
        return {
            "call_id": call_session_id,
            "status": conversation.status,
            "language": conversation.language,
            "phase": conversation.status,
            "messages": [
                {
                    "type": msg.message_type,
                    "content": msg.content,
                    "language": msg.language,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in conversation.messages
                if msg.message_type in ["language_prompt", "language_confirmation", "greeting"]
            ]
        }

    def _normalize_language(self, input_value: str) -> Language | None:
        """Normalize language input (number, name, code) to Language enum"""
        return LANGUAGE_MAP.get(input_value)

    def _get_call(self, call_session_id: int) -> CallSession:
        """Get call session or raise exception"""
        call = self.db.query(CallSession).filter(
            CallSession.id == call_session_id
        ).first()
        if not call:
            raise NotFoundException("Call session not found")
        return call

    def _get_conversation(self, call_session_id: int) -> Conversation | None:
        """Get conversation for call session"""
        return self.db.query(Conversation).filter(
            Conversation.call_session_id == call_session_id
        ).first()

    def _ensure_conversation(self, call_session_id: int) -> Conversation:
        """Get or create conversation"""
        conversation = self._get_conversation(call_session_id)
        if conversation:
            return conversation
        
        call = self._get_call(call_session_id)
        conversation = Conversation(
            call_session_id=call_session_id,
            status=GreetingPhase.LANGUAGE_SELECTION.value,
            total_questions=0,
            current_question_index=0,
            completion_percentage=0,
            profile_json=json.dumps(self._empty_profile(call))
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def _empty_profile(self, call: CallSession) -> dict:
        """Create empty profile with basic call info"""
        return {
            "call_id": call.id,
            "caller_number": call.caller_number,
            "caller_name": call.caller_name if call.caller_name != "Unknown" else None,
            "full_name": None,
            "company_name": None,
            "email": None,
            "city": None,
            "state": None,
            "country": None,
        }

    def _add_greeting_message(
        self,
        conversation: Conversation,
        phase: GreetingPhase,
        content: str,
        status: str,
        language: str | None = None
    ) -> None:
        """Add a greeting phase message to conversation"""
        message = ConversationMessage(
            conversation_id=conversation.id,
            call_session_id=conversation.call_session_id,
            speaker="AI",
            message_type="greeting",
            content=content,
            language=language,
            question_index=None,
            question_key=None
        )
        self.db.add(message)
        self.db.flush()
        
        logger.debug(
            "Greeting message added: phase=%s, status=%s, language=%s",
            phase.value,
            status,
            language
        )
