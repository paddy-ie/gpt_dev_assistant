from datetime import datetime
from typing import Iterable, Optional

from sqlmodel import Session, select

from app.models.run import Run, RunEvent, RunStatus, RunStep
from app.telemetry import get_telemetry_hub


class RunService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, *, owner_id: int, repo_label: str, goal: str, max_runtime_minutes: int) -> Run:
        run = Run(
            owner_id=owner_id,
            repo_label=repo_label,
            goal=goal,
            max_runtime_minutes=max_runtime_minutes,
            status=RunStatus.PENDING,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def list_runs(self, owner_id: Optional[int] = None, limit: int = 20) -> Iterable[Run]:
        statement = select(Run).order_by(Run.created_at.desc()).limit(limit)
        if owner_id is not None:
            statement = statement.where(Run.owner_id == owner_id)
        return self.session.exec(statement).all()

    def get_run(self, run_id: int) -> Optional[Run]:
        return self.session.get(Run, run_id)

    def get_step(self, step_id: int) -> Optional[RunStep]:
        return self.session.get(RunStep, step_id)

    def update_status(self, run: Run, status: RunStatus) -> Run:
        run.status = status
        if status == RunStatus.PLANNING and not run.started_at:
            run.started_at = datetime.utcnow()
        if status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
            run.finished_at = datetime.utcnow()
        run.updated_at = datetime.utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def append_event(
        self,
        run_id: int,
        *,
        step_id: Optional[int],
        type_: str,
        level: str,
        message: str,
        payload_json: Optional[str] = None,
    ) -> RunEvent:
        statement = select(RunEvent.sequence).where(RunEvent.run_id == run_id).order_by(RunEvent.sequence.desc()).limit(1)
        last_sequence = self.session.exec(statement).first() or 0
        event = RunEvent(
            run_id=run_id,
            step_id=step_id,
            type=type_,
            level=level,
            message=message,
            payload_json=payload_json,
            sequence=last_sequence + 1,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        hub = get_telemetry_hub()
        hub.publish(run_id, event.model_dump())
        return event

    def create_step(self, *, run_id: int, parent_id: Optional[int], type_: str, summary: str) -> RunStep:
        step = RunStep(run_id=run_id, parent_id=parent_id, type=type_, summary=summary)
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step

    def set_step_status(
        self,
        step: RunStep,
        status: RunStatus,
        *,
        summary: Optional[str] = None,
        llm_output: Optional[str] = None,
    ) -> RunStep:
        step.status = status
        if summary is not None:
            step.summary = summary
        if llm_output is not None:
            step.llm_output = llm_output
        step.updated_at = datetime.utcnow()
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step

    def list_events(
        self,
        run_id: int,
        *,
        limit: int = 500,
        after_sequence: Optional[int] = None,
    ) -> Iterable[RunEvent]:
        statement = select(RunEvent).where(RunEvent.run_id == run_id)
        if after_sequence is not None:
            statement = statement.where(RunEvent.sequence > after_sequence)
        statement = statement.order_by(RunEvent.sequence).limit(limit)
        return self.session.exec(statement).all()

    def list_steps(self, run_id: int) -> Iterable[RunStep]:
        statement = select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.created_at)
        return self.session.exec(statement).all()
