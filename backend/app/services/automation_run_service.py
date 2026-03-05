from datetime import datetime
from typing import Iterable, Optional

from sqlmodel import Session, select

from app.models.automation import AutomationRun, AutomationRunStatus


class AutomationRunService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        automation_id: int,
        triggered_by: Optional[int],
        scheduled_for: Optional[datetime] = None,
    ) -> AutomationRun:
        run = AutomationRun(
            automation_id=automation_id,
            triggered_by=triggered_by,
            status=AutomationRunStatus.PENDING,
            scheduled_for=scheduled_for,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_run(self, run_id: int) -> Optional[AutomationRun]:
        return self.session.get(AutomationRun, run_id)

    def list_runs(self, automation_id: int, limit: int = 20) -> Iterable[AutomationRun]:
        statement = (
            select(AutomationRun)
            .where(AutomationRun.automation_id == automation_id)
            .order_by(AutomationRun.created_at.desc())
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def mark_running(self, run: AutomationRun) -> AutomationRun:
        run.status = AutomationRunStatus.RUNNING
        run.started_at = datetime.utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_completed(self, run: AutomationRun, output_json: str | None = None) -> AutomationRun:
        run.status = AutomationRunStatus.COMPLETED
        run.finished_at = datetime.utcnow()
        run.output_json = output_json
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_failed(self, run: AutomationRun, error_message: str) -> AutomationRun:
        run.status = AutomationRunStatus.FAILED
        run.finished_at = datetime.utcnow()
        run.error_message = error_message
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run
