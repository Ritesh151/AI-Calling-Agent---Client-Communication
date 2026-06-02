from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.greeting_template import (
    GreetingTemplateCreate,
    GreetingTemplateRead,
    GreetingTemplateUpdate,
)
from app.services.greeting import GreetingService

router = APIRouter()


@router.get("/", response_model=SuccessResponse[list[GreetingTemplateRead]])
def list_greetings(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[GreetingTemplateRead]]:
    service = GreetingService(db)
    templates = service.repo.get_all()
    return SuccessResponse(data=[GreetingTemplateRead.model_validate(t) for t in templates])


@router.get("/default", response_model=SuccessResponse[GreetingTemplateRead])
def get_default_greeting(
    language: str | None = None,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[GreetingTemplateRead]:
    service = GreetingService(db)
    template = service.repo.get_default(language=language)
    if not template:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("No default greeting template found")
    return SuccessResponse(data=GreetingTemplateRead.model_validate(template))


@router.post("/", response_model=SuccessResponse[GreetingTemplateRead])
def create_greeting(
    request: GreetingTemplateCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[GreetingTemplateRead]:
    service = GreetingService(db)
    if request.is_default:
        current = service.repo.get_default()
        if current:
            current.is_default = False
            db.commit()
    template = service.repo.create(**request.model_dump())
    return SuccessResponse(message="Greeting template created", data=GreetingTemplateRead.model_validate(template))


@router.put("/{greeting_id}", response_model=SuccessResponse[GreetingTemplateRead])
def update_greeting(
    greeting_id: int,
    request: GreetingTemplateUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[GreetingTemplateRead]:
    service = GreetingService(db)
    if request.is_default:
        current = service.repo.get_default()
        if current and current.id != greeting_id:
            current.is_default = False
            db.commit()
    template = service.repo.update(greeting_id, **request.model_dump(exclude_unset=True))
    if not template:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Greeting template not found")
    return SuccessResponse(message="Greeting template updated", data=GreetingTemplateRead.model_validate(template))


@router.delete("/{greeting_id}", response_model=SuccessResponse[dict])
def delete_greeting(
    greeting_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = GreetingService(db)
    deleted = service.repo.delete(greeting_id)
    if not deleted:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Greeting template not found")
    return SuccessResponse(message="Greeting template deleted", data={})
