import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from app.db.session import get_session
from app.models.automation import AutomationRunStatus, AutomationState
from app.services.automation_run_service import AutomationRunService

logger = logging.getLogger(__name__)


class AutomationRunner:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        logger.info("Starting automation runner")
        self._worker_task = asyncio.create_task(self._worker(), name="automation-runner")
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        logger.info("Stopping automation runner")
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._started = False

    async def enqueue(self, run_id: int) -> None:
        logger.debug("Queue automation run %s", run_id)
        await self._queue.put(run_id)

    async def _worker(self) -> None:
        while True:
            run_id = await self._queue.get()
            try:
                await self._process(run_id)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Error processing automation run %s", run_id)
            finally:
                self._queue.task_done()

    async def _process(self, run_id: int) -> None:
        run = await asyncio.to_thread(self._mark_running, run_id)
        if run is None:
            return
        await asyncio.sleep(0.5)
        output = {
            "result": "success",
            "automation_id": run.automation_id,
            "executed_at": datetime.utcnow().isoformat(),
        }
        await asyncio.to_thread(self._complete_run, run_id, json.dumps(output))

    def _mark_running(self, run_id: int):
        with get_session() as session:
            run_service = AutomationRunService(session)
            run = run_service.get_run(run_id)
            if not run:
                logger.warning("Automation run %s missing", run_id)
                return None
            if run.status != AutomationRunStatus.PENDING:
                return run
            automation = run.automation
            if automation is None:
                session.refresh(run, attribute_names=["automation"])
                automation = run.automation
            if automation and automation.state != AutomationState.LIVE:
                run_service.mark_failed(run, "Automation not in LIVE state")
                return None
            return run_service.mark_running(run)

    def _complete_run(self, run_id: int, output_json: str) -> None:
        with get_session() as session:
            run_service = AutomationRunService(session)
            run = run_service.get_run(run_id)
            if not run:
                return
            run_service.mark_completed(run, output_json)


_runner: Optional[AutomationRunner] = None


def get_automation_runner() -> AutomationRunner:
    global _runner
    if _runner is None:
        _runner = AutomationRunner()
    return _runner
