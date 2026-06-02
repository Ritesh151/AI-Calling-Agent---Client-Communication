from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.db.models.project_management import (
    BugReport,
    Milestone,
    Project,
    ProjectSubtask,
    ProjectTask,
    Sprint,
)
from app.schemas.common import SuccessResponse
from app.services.ai_agents import (
    get_client_manager,
    get_coordinator,
    get_cto_agent,
    get_qa_agent,
)

router = APIRouter(prefix="/projects", tags=["Projects & AI Agents"])


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    client_name: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    sprint_id: int | None = None
    priority: str = "medium"
    complexity: str = "medium"
    estimate_hours: float | None = None
    task_type: str = "feature"
    assigned_agent: str | None = None


class AgentChatRequest(BaseModel):
    message: str
    project_id: int | None = None
    context: dict | None = None


@router.get("/", response_model=SuccessResponse[list[dict]])
def list_projects(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    projects = db.query(Project).order_by(Project.created_at.desc()).limit(100).all()
    data = [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "client_name": p.client_name,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse[dict])
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    project = Project(
        name=body.name,
        description=body.description,
        client_name=body.client_name,
        owner_id=user_id,
        status="planning",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return SuccessResponse(
        message="Project created",
        data={"id": project.id, "name": project.name, "status": project.status},
    )


@router.get("/{project_id}/tasks", response_model=SuccessResponse[list[dict]])
def list_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    tasks = (
        db.query(ProjectTask)
        .filter(ProjectTask.project_id == project_id)
        .order_by(ProjectTask.created_at.desc())
        .all()
    )
    return SuccessResponse(
        data=[
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "complexity": t.complexity,
                "estimate_hours": t.estimate_hours,
                "progress": t.progress,
                "assigned_agent": t.assigned_agent,
            }
            for t in tasks
        ]
    )


@router.post("/{project_id}/tasks", response_model=SuccessResponse[dict])
def create_task(
    project_id: int,
    body: TaskCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    task = ProjectTask(
        project_id=project_id,
        sprint_id=body.sprint_id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        complexity=body.complexity,
        estimate_hours=body.estimate_hours,
        task_type=body.task_type,
        assigned_agent=body.assigned_agent,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return SuccessResponse(data={"id": task.id, "title": task.title, "status": task.status})


@router.post("/agents/coordinator/chat", response_model=SuccessResponse[dict])
async def coordinator_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    agent = get_coordinator(db)
    ctx = body.context or {}
    if body.project_id:
        ctx["project_id"] = body.project_id
    result = await agent.process(body.message, ctx)
    return SuccessResponse(data=result)


@router.post("/agents/client/chat", response_model=SuccessResponse[dict])
async def client_agent_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    agent = get_client_manager(db)
    ctx = body.context or {}
    if body.project_id:
        ctx["project_id"] = body.project_id
    result = await agent.process(body.message, ctx)
    return SuccessResponse(data=result)


@router.post("/agents/cto/chat", response_model=SuccessResponse[dict])
async def cto_agent_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    agent = get_cto_agent(db)
    ctx = body.context or {}
    if body.project_id:
        ctx["project_id"] = body.project_id
    result = await agent.process(body.message, ctx)
    return SuccessResponse(data=result)


@router.post("/agents/qa/scan", response_model=SuccessResponse[dict])
async def qa_scan(
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    agent = get_qa_agent(db)
    result = await agent.process("run health scan", {"project_id": project_id})
    return SuccessResponse(data=result)


@router.get("/bugs", response_model=SuccessResponse[list[dict]])
def list_bugs(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[dict]]:
    bugs = db.query(BugReport).order_by(BugReport.created_at.desc()).limit(100).all()
    return SuccessResponse(
        data=[
            {
                "id": b.id,
                "title": b.title,
                "severity": b.severity,
                "category": b.category,
                "status": b.status,
                "detected_by": b.detected_by,
            }
            for b in bugs
        ]
    )
