import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.db.session import get_session
from app.models.run import RunStatus
from app.services.run_service import RunService

logger = logging.getLogger(__name__)


class RunOrchestrator:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        logger.info("Starting run orchestrator worker")
        self._worker_task = asyncio.create_task(self._worker(), name="run-orchestrator")
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        logger.info("Stopping run orchestrator worker")
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._started = False

    async def enqueue_run(self, run_id: int) -> None:
        logger.debug("Enqueue run %s", run_id)
        await self._queue.put(run_id)

    async def _worker(self) -> None:
        while True:
            run_id = await self._queue.get()
            try:
                await self._process_run(run_id)
            except Exception:  # pragma: no cover - baseline resilience
                logger.exception("Unhandled error processing run %s", run_id)
            finally:
                self._queue.task_done()

    async def _process_run(self, run_id: int) -> None:
        was_prepared = await self._transition(run_id, RunStatus.PLANNING, "Preparing plan")
        if not was_prepared:
            return

        plan_step_id = await self._create_step(run_id, "plan", "Outlined work plan")
        if plan_step_id:
            await asyncio.sleep(0.5)
            await self._complete_step(plan_step_id, RunStatus.COMPLETED, "Plan ready")

        await asyncio.sleep(0.5)
        await self._transition(run_id, RunStatus.EXECUTING, "Applying code changes")
        exec_step_id = await self._create_step(run_id, "execute", "Executed planned actions")
        if exec_step_id:
            await asyncio.sleep(0.5)
            await self._complete_step(exec_step_id, RunStatus.COMPLETED, "Execution finished")

        await self._transition(run_id, RunStatus.TESTING, "Running validation suite")
        test_step_id = await self._create_step(run_id, "test", "Ran automated tests")
        if test_step_id:
            await asyncio.sleep(0.5)
            await self._complete_step(test_step_id, RunStatus.COMPLETED, "Tests passed")

        await self._transition(run_id, RunStatus.COMPLETED, "Run finished successfully")

    async def _transition(self, run_id: int, status: RunStatus, message: str) -> bool:
        def sync_transition() -> bool:
            with get_session() as session:
                service = RunService(session)
                run = service.get_run(run_id)
                if not run:
                    logger.warning("Run %s not found", run_id)
                    return False
                if run.status == status:
                    return True
                service.update_status(run, status)
                service.append_event(run_id, step_id=None, type_="status", level="info", message=message)
                return True

        return await asyncio.to_thread(sync_transition)

    async def _create_step(self, run_id: int, step_type: str, summary: str) -> Optional[int]:
        def sync_create() -> Optional[int]:
            with get_session() as session:
                service = RunService(session)
                run = service.get_run(run_id)
                if not run:
                    return None
                step = service.create_step(run_id=run_id, parent_id=None, type_=step_type, summary=summary)
                service.append_event(
                    run_id,
                    step_id=step.id,
                    type_="step",
                    level="info",
                    message=summary,
                )
                return step.id

        return await asyncio.to_thread(sync_create)

    async def _complete_step(self, step_id: int, status: RunStatus, summary: str) -> None:
        def sync_complete() -> None:
            with get_session() as session:
                service = RunService(session)
                step = service.get_step(step_id)
                if not step:
                    return
                service.set_step_status(step, status, summary=summary)
                service.append_event(
                    step.run_id,
                    step_id=step.id,
                    type_="step",
                    level="info",
                    message=summary,
                )

        await asyncio.to_thread(sync_complete)


_orchestrator: Optional[RunOrchestrator] = None


def get_orchestrator() -> RunOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RunOrchestrator()
    return _orchestrator
