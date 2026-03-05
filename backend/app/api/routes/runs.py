from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.deps import get_db_session
from app.models.run import RunStatus
from app.orchestrator import get_orchestrator
from app.schemas.run import RunCreate, RunEventRead, RunRead, RunStepRead
from app.security.dependencies import get_current_user
from app.services.run_service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    start: bool = True,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> RunRead:
    service = RunService(session)
    run = service.create_run(
        owner_id=current_user.id,
        repo_label=payload.repo_label,
        goal=payload.goal,
        max_runtime_minutes=payload.max_runtime_minutes,
    )
    service.append_event(run.id, step_id=None, type_="status", level="info", message="Run queued")
    if start:
        orchestrator = get_orchestrator()
        await orchestrator.enqueue_run(run.id)
    return RunRead.from_orm(run)


@router.get("/", response_model=list[RunRead])
async def list_runs(
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[RunRead]:
    service = RunService(session)
    runs = service.list_runs(owner_id=current_user.id)
    return [RunRead.from_orm(run) for run in runs]


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: int,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> RunRead:
    service = RunService(session)
    run = service.get_run(run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunRead.from_orm(run)


@router.get("/{run_id}/events", response_model=list[RunEventRead])
async def get_run_events(
    run_id: int,
    after: int | None = None,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[RunEventRead]:
    service = RunService(session)
    run = service.get_run(run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    events = service.list_events(run_id, after_sequence=after)
    return [RunEventRead.from_orm(event) for event in events]


@router.get("/{run_id}/steps", response_model=list[RunStepRead])
async def get_run_steps(
    run_id: int,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[RunStepRead]:
    service = RunService(session)
    run = service.get_run(run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    steps = service.list_steps(run_id)
    return [RunStepRead.from_orm(step) for step in steps]


@router.post("/{run_id}/restart", response_model=RunRead)
async def restart_run(
    run_id: int,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> RunRead:
    service = RunService(session)
    run = service.get_run(run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if run.status not in {RunStatus.FAILED, RunStatus.STALLED, RunStatus.COMPLETED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run is already in progress")
    run.status = RunStatus.PENDING
    run.started_at = None
    run.finished_at = None
    run.updated_at = datetime.utcnow()
    session.add(run)
    session.commit()
    session.refresh(run)
    service.append_event(run.id, step_id=None, type_="status", level="info", message="Run re-queued")
    orchestrator = get_orchestrator()
    await orchestrator.enqueue_run(run.id)
    return RunRead.from_orm(run)
