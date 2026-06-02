from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.db.models.call_session import CallSession
from app.db.models.conversation import Conversation, ConversationMessage
from app.services.project_planning import ProjectPlanningService
from app.schemas.conversation import ConversationRead
from app.services.call_conversation.question_engine import (
    SERVICE_SELECTION_QUESTION,
    base_questions,
    normalize_language,
    normalize_service_type,
    question_at,
    questions_for,
    service_label,
)
from app.services.event_bus import Event, EventPriority, event_bus
from app.services.mongo_storage import mongo_storage
from app.services.greeting_engine import GreetingEngine, GreetingPhase

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def ensure_for_call(self, call_session_id: int) -> ConversationRead:
        call = self._get_call(call_session_id)
        conversation = self._get_conversation(call_session_id)
        if conversation:
            return ConversationRead.model_validate(conversation)

        conversation = Conversation(
            call_session_id=call_session_id,
            status="language_selection",
            total_questions=len(base_questions()),
            current_question_index=0,
            completion_percentage=0,
            profile_json=json.dumps(self._empty_profile(call)),
            started_at=datetime.now(UTC),
        )
        self.db.add(conversation)
        self.db.flush()

        self._add_message(
            conversation,
            speaker="AI",
            message_type="language_prompt",
            content=LANGUAGE_SELECTION_GREETING,
            language=None,
        )
        self._refresh_transcript(conversation)
        self.db.commit()
        await self._broadcast(conversation, call)
        self._mirror(conversation, call)
        return ConversationRead.model_validate(conversation)

    async def select_language(self, call_session_id: int, language: str) -> ConversationRead:
        call = self._get_call(call_session_id)
        conversation = await self._ensure_model(call_session_id)
        selected = normalize_language(language)

        call.language = selected
        conversation.language = selected
        conversation.status = "in_progress"
        conversation.total_questions = len(base_questions())
        conversation.current_question_index = 0
        conversation.completion_percentage = 0

        first_question = question_at(0)
        if first_question:
            self._add_message(
                conversation,
                speaker="AI",
                message_type="question",
                content=first_question.text,
                language=selected,
                question_index=1,
                question_key=first_question.key,
            )

        self._refresh_transcript(conversation)
        self.db.commit()
        await self._broadcast(conversation, call)
        self._mirror(conversation, call)
        return ConversationRead.model_validate(conversation)

    async def record_answer(self, call_session_id: int, answer: str) -> ConversationRead:
        call = self._get_call(call_session_id)
        conversation = await self._ensure_model(call_session_id)
        language = conversation.language or "english"
        current_question = question_at(conversation.current_question_index, conversation.service_type)
        question_key = current_question.key if current_question else None

        self._add_message(
            conversation,
            speaker="USER",
            message_type="answer",
            content=answer,
            language=language,
            question_index=conversation.current_question_index + 1,
            question_key=question_key,
        )

        if question_key == SERVICE_SELECTION_QUESTION.key:
            conversation.service_type = normalize_service_type(answer)
            conversation.total_questions = len(questions_for(conversation.service_type))

        self._update_profile(conversation, call)
        conversation.current_question_index += 1
        self._update_completion(conversation)

        next_question = question_at(conversation.current_question_index, conversation.service_type)
        if next_question:
            self._add_message(
                conversation,
                speaker="AI",
                message_type="question",
                content=next_question.text,
                language=language,
                question_index=conversation.current_question_index + 1,
                question_key=next_question.key,
            )
        else:
            conversation.status = "qualified"
            conversation.completed_at = datetime.now(UTC)
            self._analyze_requirements(conversation)
            self._create_client_database(conversation, call)
            self._create_project_package(conversation, call)

        self._refresh_transcript(conversation)
        self.db.commit()
        await self._broadcast(conversation, call)
        self._mirror(conversation, call)
        return ConversationRead.model_validate(conversation)

    def get_by_call(self, call_session_id: int) -> ConversationRead:
        conversation = self._get_conversation(call_session_id)
        if not conversation:
            raise NotFoundException("Conversation not found for this call")
        return ConversationRead.model_validate(conversation)

    def get_current(self) -> ConversationRead | None:
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.status.in_(["language_selection", "in_progress", "qualified"]))
            .order_by(Conversation.created_at.desc())
            .first()
        )
        return ConversationRead.model_validate(conversation) if conversation else None

    async def _ensure_model(self, call_session_id: int) -> Conversation:
        await self.ensure_for_call(call_session_id)
        conversation = self._get_conversation(call_session_id)
        if not conversation:
            raise NotFoundException("Conversation not found for this call")
        return conversation

    def _get_conversation(self, call_session_id: int) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .filter(Conversation.call_session_id == call_session_id)
            .first()
        )

    def _get_call(self, call_session_id: int) -> CallSession:
        call = self.db.query(CallSession).filter(CallSession.id == call_session_id).first()
        if not call:
            raise NotFoundException("Call session not found")
        return call

    def _add_message(
        self,
        conversation: Conversation,
        *,
        speaker: str,
        message_type: str,
        content: str,
        language: str | None,
        question_index: int | None = None,
        question_key: str | None = None,
    ) -> None:
        self.db.add(
            ConversationMessage(
                conversation_id=conversation.id,
                call_session_id=conversation.call_session_id,
                speaker=speaker,
                message_type=message_type,
                content=content,
                language=language,
                question_index=question_index,
                question_key=question_key,
            )
        )
        self.db.flush()
        self.db.refresh(conversation)

    def _answer_map(self, conversation: Conversation) -> dict[str, str]:
        return {
            message.question_key: message.content
            for message in conversation.messages
            if message.speaker == "USER" and message.question_key
        }

    def _empty_profile(self, call: CallSession) -> dict[str, str | None]:
        return {
            "full_name": call.caller_name if call.caller_name != "Unknown" else None,
            "company_name": None,
            "phone": call.caller_number,
            "email": None,
            "city": None,
            "state": None,
            "country": None,
            "business_category": None,
            "years_in_business": None,
            "website": None,
            "budget": None,
            "timeline": None,
            "preferred_contact_method": None,
        }

    def _update_profile(self, conversation: Conversation, call: CallSession) -> None:
        profile = self._empty_profile(call)
        try:
            profile.update(json.loads(conversation.profile_json or "{}"))
        except json.JSONDecodeError:
            pass
        answers = self._answer_map(conversation)
        for key in profile:
            if key in answers:
                profile[key] = answers[key]
        profile["phone"] = profile.get("phone") or call.caller_number
        conversation.profile_json = json.dumps(profile, ensure_ascii=False)
        if profile.get("full_name"):
            call.caller_name = str(profile["full_name"])

    def _update_completion(self, conversation: Conversation) -> None:
        total = max(conversation.total_questions, 1)
        conversation.completion_percentage = min(
            100, round((conversation.current_question_index / total) * 100)
        )

    def _analyze_requirements(self, conversation: Conversation) -> None:
        answers = self._answer_map(conversation)
        service = service_label(conversation.service_type) or answers.get("service_type", "Other")
        service_answers = {
            key: value
            for key, value in answers.items()
            if key not in {question.key for question in base_questions()}
        }
        profile = self._profile(conversation)

        analysis = {
            "service_type": service,
            "business_requirements": [
                f"Deliver {service} for {profile.get('company_name') or profile.get('full_name') or 'the client'}.",
                f"Support business category: {profile.get('business_category') or 'not specified'}.",
                f"Target timeline: {profile.get('timeline') or 'not specified'}.",
                f"Planned budget: {profile.get('budget') or 'not specified'}.",
            ],
            "functional_requirements": self._functional_requirements(service_answers),
            "non_functional_requirements": [
                "Responsive and reliable user experience.",
                "Secure handling of client and user data.",
                "Maintainable architecture suitable for future enhancements.",
                "Admin-friendly reporting or management where applicable.",
            ],
            "integrations": self._extract_integrations(service_answers),
            "target_users": self._extract_target_users(service_answers, profile),
            "constraints": self._extract_constraints(profile, service_answers),
            "risks": self._extract_risks(profile, service_answers),
            "dependencies": self._extract_dependencies(profile, service_answers),
            "captured_answers": service_answers,
        }
        conversation.requirements_json = json.dumps(analysis, ensure_ascii=False)

    def _functional_requirements(self, answers: dict[str, str]) -> list[str]:
        requirements = []
        for key, value in answers.items():
            label = key.replace("_", " ").title()
            requirements.append(f"{label}: {value}")
        return requirements or ["Detailed functionality to be confirmed in follow-up."]

    def _extract_integrations(self, answers: dict[str, str]) -> list[str]:
        integrations = [
            value
            for key, value in answers.items()
            if "integration" in key or "channels" in key or "payment" in value.lower()
        ]
        return integrations or ["No integrations confirmed yet."]

    def _extract_target_users(self, answers: dict[str, str], profile: dict) -> list[str]:
        users = [
            value
            for key, value in answers.items()
            if "users" in key or "roles" in key or "audience" in key or "departments" in key
        ]
        if profile.get("business_category"):
            users.append(f"{profile['business_category']} customers/team")
        return users or ["Target users to be clarified."]

    def _extract_constraints(self, profile: dict, answers: dict[str, str]) -> list[str]:
        constraints = []
        if profile.get("budget"):
            constraints.append(f"Budget: {profile['budget']}")
        if profile.get("timeline"):
            constraints.append(f"Timeline: {profile['timeline']}")
        for key, value in answers.items():
            if "existing" in key or "content_ready" in key:
                constraints.append(value)
        return constraints or ["No explicit constraints captured."]

    def _extract_risks(self, profile: dict, answers: dict[str, str]) -> list[str]:
        risks = []
        if not profile.get("budget"):
            risks.append("Budget not confirmed.")
        if not profile.get("timeline"):
            risks.append("Timeline not confirmed.")
        if any("not ready" in value.lower() for value in answers.values()):
            risks.append("Required client assets may not be ready.")
        return risks or ["No major risks identified from the call."]

    def _extract_dependencies(self, profile: dict, answers: dict[str, str]) -> list[str]:
        dependencies = []
        if profile.get("website"):
            dependencies.append(f"Existing website/domain details: {profile['website']}")
        for key, value in answers.items():
            if "content" in key or "knowledge" in key or "assets" in key:
                dependencies.append(value)
        return dependencies or ["Client confirmation and follow-up documentation."]

    def _create_client_database(self, conversation: Conversation, call: CallSession) -> None:
        profile = self._profile(conversation)
        slug = self._client_slug(profile)
        conversation.client_slug = slug
        conversation.client_database = f"client_{slug.lower()}"
        mongo_storage.create_client_database(
            db_name=conversation.client_database,
            payload=self._document(conversation, call),
        )

    def _create_project_package(self, conversation: Conversation, call: CallSession) -> None:
        requirements = self._requirements(conversation)
        if requirements.get("project_id"):
            return
        try:
            project = ProjectPlanningService(self.db).generate_project_from_conversation(conversation, call)
            requirements["project_id"] = project.id
            requirements["project_generated_at"] = datetime.now(UTC).isoformat()
            conversation.requirements_json = json.dumps(requirements, ensure_ascii=False)
        except Exception as exc:
            logger.error("Error generating project package: %s", exc)

    def _client_slug(self, profile: dict) -> str:
        company = str(profile.get("company_name") or "RG")
        name = str(profile.get("full_name") or "CLIENT")
        seed = f"{company}_{name}"
        slug = re.sub(r"[^A-Za-z0-9]+", "_", seed).strip("_").upper()
        return slug or "RG_CLIENT"

    def _profile(self, conversation: Conversation) -> dict:
        try:
            return json.loads(conversation.profile_json or "{}")
        except json.JSONDecodeError:
            return {}

    def _requirements(self, conversation: Conversation) -> dict:
        try:
            return json.loads(conversation.requirements_json or "{}")
        except json.JSONDecodeError:
            return {}

    def _refresh_transcript(self, conversation: Conversation) -> None:
        self.db.refresh(conversation)
        lines = [f"{message.speaker}: {message.content}" for message in conversation.messages]
        conversation.transcript = "\n".join(lines)

    async def _broadcast(self, conversation: Conversation, call: CallSession) -> None:
        await event_bus.publish(
            Event(
                type="conversation_updated",
                priority=EventPriority.HIGH,
                data=self._document(conversation, call),
            )
        )

    def _mirror(self, conversation: Conversation, call: CallSession) -> None:
        mongo_storage.upsert_call_document(self._document(conversation, call))

    def _document(self, conversation: Conversation, call: CallSession) -> dict:
        self.db.refresh(conversation)
        profile = self._profile(conversation)
        requirements = self._requirements(conversation)
        messages = [
            {
                "speaker": message.speaker,
                "message_type": message.message_type,
                "content": message.content,
                "language": message.language,
                "question_index": message.question_index,
                "question_key": message.question_key,
                "timestamp": message.created_at.isoformat() if message.created_at else None,
            }
            for message in conversation.messages
        ]
        captured = [
            item
            for section in (
                requirements.get("business_requirements", []),
                requirements.get("functional_requirements", []),
                requirements.get("non_functional_requirements", []),
                requirements.get("integrations", []),
            )
            for item in (section if isinstance(section, list) else [section])
        ]
        return {
            "call_id": call.id,
            "call_session_id": call.id,
            "device_id": call.device_id,
            "caller_number": call.caller_number,
            "caller_name": call.caller_name,
            "language": conversation.language,
            "service_type": conversation.service_type,
            "service_label": service_label(conversation.service_type),
            "client_slug": conversation.client_slug,
            "client_database": conversation.client_database,
            "client_profile": profile,
            "requirements_analysis": requirements,
            "call_status": call.call_status,
            "conversation_id": conversation.id,
            "conversation_status": conversation.status,
            "completion_percentage": conversation.completion_percentage,
            "question_progress": {
                "current": conversation.current_question_index,
                "total": conversation.total_questions,
            },
            "budget": profile.get("budget"),
            "timeline": profile.get("timeline"),
            "requirements_captured": captured,
            "conversation": messages,
            "transcript": conversation.transcript,
        }
