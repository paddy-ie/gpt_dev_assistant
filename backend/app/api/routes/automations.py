from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import Session

from app.automations.runner import get_automation_runner
from app.db.deps import get_db_session
from app.models.automation import AutomationState
from app.schemas.automation import (
    AutomationCreate,
    AutomationRead,
    AutomationRunCreate,
    AutomationRunRead,
    AutomationUpdate,
)
from app.security.dependencies import get_current_user
from app.services.automation_run_service import AutomationRunService
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/automations", tags=["automations"])


@router.post("/", response_model=AutomationRead, status_code=status.HTTP_201_CREATED)
async def create_automation(
    payload: AutomationCreate,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AutomationRead:
    service = AutomationService(session)
    automation = service.create(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        config_json=payload.config_json,
    )
    return AutomationRead.from_orm(automation)


@router.get("/", response_model=list[AutomationRead])
async def list_automations(
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[AutomationRead]:
    service = AutomationService(session)
    automations = service.list(owner_id=current_user.id)
    return [AutomationRead.from_orm(item) for item in automations]


@router.patch("/{automation_id}", response_model=AutomationRead)
async def update_automation(
    automation_id: int,
    payload: AutomationUpdate,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AutomationRead:
    service = AutomationService(session)
    automation = service.get(automation_id)
    if not automation or automation.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    if payload.state is not None:
        automation = service.update_state(automation, state=payload.state)
    automation = service.update_config(
        automation,
        description=payload.description,
        config_json=payload.config_json,
    )
    return AutomationRead.from_orm(automation)


@router.post("/{automation_id}/publish", response_model=AutomationRead)
async def publish_automation(
    automation_id: int,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AutomationRead:
    service = AutomationService(session)
    automation = service.get(automation_id)
    if not automation or automation.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    automation = service.update_state(automation, state=AutomationState.LIVE)
    return AutomationRead.from_orm(automation)


@router.get("/{automation_id}/runs", response_model=list[AutomationRunRead])
async def list_automation_runs(
    automation_id: int,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[AutomationRunRead]:
    automation_service = AutomationService(session)
    automation = automation_service.get(automation_id)
    if not automation or automation.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    run_service = AutomationRunService(session)
    runs = run_service.list_runs(automation_id)
    return [AutomationRunRead.from_orm(item) for item in runs]


@router.post("/{automation_id}/runs", response_model=AutomationRunRead, status_code=status.HTTP_201_CREATED)
async def trigger_automation_run(
    automation_id: int,
    payload: AutomationRunCreate = Body(default_factory=AutomationRunCreate),
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AutomationRunRead:
    automation_service = AutomationService(session)
    automation = automation_service.get(automation_id)
    if not automation or automation.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    run_service = AutomationRunService(session)
    run = run_service.create_run(
        automation_id=automation_id,
        triggered_by=current_user.id,
        scheduled_for=payload.scheduled_for,
    )
    runner = get_automation_runner()
    if automation.state == AutomationState.LIVE and payload.scheduled_for is None:
        await runner.enqueue(run.id)
    return AutomationRunRead.from_orm(run)
