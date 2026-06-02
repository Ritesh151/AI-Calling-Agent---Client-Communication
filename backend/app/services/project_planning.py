from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.db.models.call_session import CallSession
from app.db.models.conversation import Conversation
from app.db.models.project_management import (
    Milestone,
    Project,
    ProjectSubtask,
    ProjectTask,
)
from app.services.call_conversation.question_engine import service_label
from app.services.mongo_storage import mongo_storage


class ProjectPlanningService:
    RATE_PER_HOUR = 120
    DEFAULT_DURATION_WEEKS = 6

    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_project_from_conversation(
        self,
        conversation: Conversation,
        call: CallSession,
    ) -> Project:
        profile = self._profile(conversation)
        requirements = self._requirements(conversation)
        project_name = self._project_name(profile, requirements, conversation)
        project_description = self._project_description(profile, requirements)
        project = Project(
            name=project_name,
            description=project_description,
            client_name=profile.get("company_name") or profile.get("full_name"),
            budget_estimate=self._parse_budget(profile.get("budget")),
            target_delivery=self._parse_timeline(profile.get("timeline")),
            status="planning",
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        self._create_milestones(project, requirements)
        self._create_tasks(project, requirements)
        self.db.commit()

        proposal = self._create_proposal(project, conversation, call, profile, requirements)
        mongo_storage.upsert_project_document(
            {
                "project_id": project.id,
                "call_id": call.id,
                "conversation_id": conversation.id,
                "project_name": project.name,
                "client_profile": profile,
                "project_summary": proposal["project_summary"],
                "project_scope": proposal["project_scope"],
                "goals": proposal["goals"],
                "deliverables": proposal["deliverables"],
                "timeline_estimate": proposal["timeline_estimate"],
                "cost_estimate": proposal["cost_estimate"],
                "technology_stack": proposal["technology_stack"],
                "milestones": proposal["milestones"],
                "risks": proposal["risks"],
                "dependencies": proposal["dependencies"],
                "documents": proposal["documents"],
            }
        )

        mongo_storage.upsert_proposal_document(
            {
                "project_id": project.id,
                "call_id": call.id,
                "conversation_id": conversation.id,
                "project_name": project.name,
                "client_name": project.client_name,
                "proposal": proposal,
            }
        )
        return project

    def _project_name(
        self,
        profile: dict[str, Any],
        requirements: dict[str, Any],
        conversation: Conversation,
    ) -> str:
        service = service_label(conversation.service_type) or "AI Project"
        client_name = profile.get("company_name") or profile.get("full_name") or "Client"
        return f"{service} for {client_name}"

    def _project_description(self, profile: dict[str, Any], requirements: dict[str, Any]) -> str:
        summary = requirements.get("service_type") or "Unspecified service"
        client_name = profile.get("company_name") or profile.get("full_name") or "the client"
        return (
            f"Deliver a {summary.lower()} solution for {client_name}, including requirements capture, planning, implementation, and a compelling proposal."
        )

    def _parse_budget(self, budget: str | None) -> float | None:
        if not budget:
            return None
        cleaned = re.sub(r"[^0-9.]", "", budget)
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_timeline(self, timeline: str | None) -> datetime | None:
        if not timeline:
            return None
        timeline_lower = timeline.lower()
        now = datetime.now()
        if "month" in timeline_lower:
            match = re.search(r"(\d+)", timeline_lower)
            weeks = int(match.group(1)) * 4 if match else self.DEFAULT_DURATION_WEEKS
        elif "week" in timeline_lower:
            match = re.search(r"(\d+)", timeline_lower)
            weeks = int(match.group(1)) if match else self.DEFAULT_DURATION_WEEKS
        elif "day" in timeline_lower:
            match = re.search(r"(\d+)", timeline_lower)
            days = int(match.group(1)) if match else 7
            weeks = max(1, days // 7)
        else:
            weeks = self.DEFAULT_DURATION_WEEKS
        return now + timedelta(weeks=weeks)

    def _create_milestones(self, project: Project, requirements: dict[str, Any]) -> None:
        titles = [
            "Discovery & Requirements",
            "Design & Architecture",
            "Implementation & Integration",
            "Testing & Delivery",
        ]
        start = datetime.now()
        for index, title in enumerate(titles):
            due_date = start + timedelta(weeks=(index + 1) * 2)
            milestone = Milestone(
                project_id=project.id,
                title=title,
                description=f"{title} phase for the project.",
                due_date=due_date,
                status="planned",
                progress=0,
            )
            self.db.add(milestone)
        self.db.flush()

    def _create_tasks(self, project: Project, requirements: dict[str, Any]) -> None:
        functional = requirements.get("functional_requirements", []) or []
        nonfunctional = requirements.get("non_functional_requirements", []) or []
        integrations = requirements.get("integrations", []) or []
        all_tasks = []

        for requirement in functional:
            all_tasks.append(
                {
                    "title": requirement,
                    "description": requirement,
                    "task_type": "feature",
                    "estimate_hours": 16,
                }
            )

        if nonfunctional:
            all_tasks.append(
                {
                    "title": "Non-functional requirements implementation",
                    "description": "Implement performance, security, and reliability requirements.",
                    "task_type": "quality",
                    "estimate_hours": 12,
                }
            )

        if integrations:
            all_tasks.append(
                {
                    "title": "Integration delivery",
                    "description": f"Implement integrations: {', '.join(integrations)}.",
                    "task_type": "integration",
                    "estimate_hours": 14,
                }
            )

        if not all_tasks:
            all_tasks.append(
                {
                    "title": "Discovery and requirements follow-up",
                    "description": "Refine requirements and prepare project documentation.",
                    "task_type": "research",
                    "estimate_hours": 10,
                }
            )

        for task_data in all_tasks:
            task = ProjectTask(
                project_id=project.id,
                title=task_data["title"],
                description=task_data["description"],
                task_type=task_data["task_type"],
                priority="medium",
                complexity="medium",
                estimate_hours=task_data["estimate_hours"],
                status="todo",
                progress=0,
            )
            self.db.add(task)
            self.db.flush()
            self._create_subtasks(task)

    def _create_subtasks(self, task: ProjectTask) -> None:
        subtasks = [
            "Define scope and acceptance criteria",
            "Implement core behavior",
            "Review and refine deliverable",
        ]
        for title in subtasks:
            self.db.add(
                ProjectSubtask(
                    task_id=task.id,
                    title=title,
                    status="todo",
                    progress=0,
                )
            )
        self.db.flush()

    def _create_proposal(
        self,
        project: Project,
        conversation: Conversation,
        call: CallSession,
        profile: dict[str, Any],
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        service = requirements.get("service_type") or service_label(conversation.service_type) or "Custom service"
        summary = (
            f"Create and deliver a {service.lower()} solution for "
            f"{profile.get('company_name') or profile.get('full_name') or 'the client'}."
        )
        deliverables = [task.title for task in self.db.query(ProjectTask).filter(ProjectTask.project_id == project.id).all()]
        cost = self._estimate_cost(project)
        proposal = {
            "project_name": project.name,
            "project_summary": summary,
            "project_scope": self._build_scope(requirements, profile),
            "goals": self._build_goals(requirements, profile),
            "deliverables": deliverables,
            "timeline_estimate": self._format_timeline(project, profile),
            "cost_estimate": f"${cost:,}",
            "technology_stack": self._technology_stack(service),
            "milestones": [
                {
                    "title": m.title,
                    "description": m.description,
                    "due_date": m.due_date.isoformat() if m.due_date else None,
                }
                for m in self.db.query(Milestone).filter(Milestone.project_id == project.id).all()
            ],
            "risks": requirements.get("risks", []),
            "dependencies": requirements.get("dependencies", []),
            "documents": self._build_documents(project, requirements, profile),
        }
        return proposal

    def _estimate_cost(self, project: Project) -> int:
        tasks = self.db.query(ProjectTask).filter(ProjectTask.project_id == project.id).all()
        hours = sum((task.estimate_hours or 8) for task in tasks)
        return int(hours * self.RATE_PER_HOUR)

    def _format_timeline(self, project: Project, profile: dict[str, Any]) -> str:
        if project.target_delivery:
            return project.target_delivery.isoformat()
        if profile.get("timeline"):
            return str(profile["timeline"])
        return f"{self.DEFAULT_DURATION_WEEKS} weeks"

    def _technology_stack(self, service_name: str) -> list[str]:
        return [
            "Next.js",
            "React",
            "Tailwind CSS",
            "FastAPI",
            "PostgreSQL",
            "MongoDB",
            "Redis",
        ]

    def _build_scope(self, requirements: dict[str, Any], profile: dict[str, Any]) -> list[str]:
        scope = []
        scope.append(requirements.get("service_type", "Define the target service offering."))
        scope.extend(requirements.get("business_requirements", []))
        scope.extend(requirements.get("functional_requirements", []))
        return scope or ["Scope to be finalized during kickoff."]

    def _build_goals(self, requirements: dict[str, Any], profile: dict[str, Any]) -> list[str]:
        goals = [
            "Capture and validate business requirements.",
            "Deliver a secure and maintainable solution.",
            "Provide a clear project timeline and cost estimate.",
        ]
        goals.extend(requirements.get("non_functional_requirements", []))
        return goals

    def _build_documents(self, project: Project, requirements: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
        client_name = profile.get("company_name") or profile.get("full_name") or "Client"
        brd = (
            f"Business Requirements Document for {client_name}:\n"
            f"Project: {project.name}\n\n"
            "Summary:\n"
            f"{requirements.get('business_requirements', ['No business requirements'])[0]}\n\n"
            "Key deliverables:\n"
            + "\n".join(f"- {item}" for item in requirements.get("functional_requirements", []))
        )
        srs = (
            f"Software Requirements Specification:\nProject: {project.name}\n\n"
            "Functional requirements:\n"
            + "\n".join(f"- {item}" for item in requirements.get("functional_requirements", []))
            + "\n\nNon-functional requirements:\n"
            + "\n".join(f"- {item}" for item in requirements.get("non_functional_requirements", []))
        )
        use_cases = (
            "Use Cases:\n"
            + "\n".join(
                f"- {user_story}" for user_story in self._build_use_cases(requirements, profile)
            )
        )
        user_stories = (
            "User Stories:\n"
            + "\n".join(
                f"- {story}" for story in self._build_user_stories(requirements, profile)
            )
        )
        acceptance = (
            "Acceptance Criteria:\n"
            + "\n".join(
                f"- {criteria}" for criteria in self._build_acceptance_criteria(requirements)
            )
        )
        return {
            "brd": brd,
            "srs": srs,
            "use_cases": use_cases,
            "user_stories": user_stories,
            "acceptance_criteria": acceptance,
        }

    def _build_use_cases(self, requirements: dict[str, Any], profile: dict[str, Any]) -> list[str]:
        users = requirements.get("target_users", []) or ["End users"]
        use_cases = []
        for user in users:
            use_cases.append(f"{user} interacts with the system to achieve a business objective.")
        return use_cases

    def _build_user_stories(self, requirements: dict[str, Any], profile: dict[str, Any]) -> list[str]:
        stories = []
        for requirement in requirements.get("functional_requirements", []):
            stories.append(
                f"As a user, I want to {requirement.lower()}, so that the system meets the business need."
            )
        if not stories:
            stories.append("As a user, I want to validate requirements so the project scope is clear.")
        return stories

    def _build_acceptance_criteria(self, requirements: dict[str, Any]) -> list[str]:
        criteria = []
        for requirement in requirements.get("functional_requirements", []):
            criteria.append(f"The system implements: {requirement}.")
        if not criteria:
            criteria.append("The requirements are reviewed and accepted by the client.")
        return criteria

    def render_proposal_pdf(self, proposal: dict[str, Any]) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(40, 760, proposal.get("project_name", "Project Proposal"))
        pdf.setFont("Helvetica", 10)
        y = 740

        sections = [
            ("Summary", proposal.get("project_summary", "")),
            ("Scope", proposal.get("project_scope", [])),
            ("Timeline", proposal.get("timeline_estimate", "")),
            ("Cost", proposal.get("cost_estimate", "")),
            ("Tech stack", proposal.get("technology_stack", [])),
            ("Milestones", proposal.get("milestones", [])),
            ("Risks", proposal.get("risks", [])),
            ("Dependencies", proposal.get("dependencies", [])),
        ]

        for title, value in sections:
            if not value:
                continue
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, f"{title}:")
            y -= 16
            pdf.setFont("Helvetica", 10)
            if isinstance(value, list):
                for item in value:
                    line = str(item)
                    pdf.drawString(50, y, f"- {line}")
                    y -= 12
                    if y < 80:
                        pdf.showPage()
                        pdf.setFont("Helvetica", 10)
                        y = 750
            else:
                for line in str(value).split("\n"):
                    pdf.drawString(50, y, line)
                    y -= 12
                    if y < 80:
                        pdf.showPage()
                        pdf.setFont("Helvetica", 10)
                        y = 750
            y -= 10

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()

    def _profile(self, conversation: Conversation) -> dict[str, Any]:
        try:
            return json.loads(conversation.profile_json or "{}")
        except json.JSONDecodeError:
            return {}

    def _requirements(self, conversation: Conversation) -> dict[str, Any]:
        try:
            return json.loads(conversation.requirements_json or "{}")
        except json.JSONDecodeError:
            return {}
