from __future__ import annotations

import threading
import time
from typing import Dict

from models import AgentJob, EventType, JobStatus
from storage import storage


class AgentRunner:
    """Background runner that simulates Agent3 behaviour (Phase 1)."""

    def __init__(self) -> None:
        self._threads: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    # ---------------------------------
    # Public API
    # ---------------------------------
    def start_job(self, job: AgentJob) -> None:
        storage.append_event(job.id, EventType.INFO, "Job created", {"goal": job.goal})
        storage.mark_status(job.id, JobStatus.PENDING)
        thread = threading.Thread(target=self._run_stub_job, args=(job.id,), daemon=True)
        with self._lock:
            self._threads[job.id] = thread
        thread.start()

    def request_stop(self, job_id: str) -> bool:
        job = storage.request_cancel(job_id)
        if not job:
            return False
        storage.append_event(job_id, EventType.INFO, "Cancellation requested")
        return True

    # ---------------------------------
    # Internal helpers
    # ---------------------------------
    def _run_stub_job(self, job_id: str) -> None:
        job = storage.mark_status(job_id, JobStatus.RUNNING)
        if not job:
            return
        storage.append_event(job_id, EventType.PLAN, "Planning job", {})
        time.sleep(0.5)

        steps = [
            "Review project files",
            "Draft plan",
            "Apply sample diff",
            "Summarize next actions",
        ]

        for idx, step in enumerate(steps, start=1):
            if self._should_cancel(job_id):
                storage.append_event(job_id, EventType.INFO, "Job cancelled mid-run", {"step": idx})
                storage.mark_status(job_id, JobStatus.CANCELED)
                return
            storage.append_event(
                job_id,
                EventType.STEP,
                f"Executing placeholder step {idx}",
                {"description": step},
            )
            time.sleep(0.5)

        storage.append_event(job_id, EventType.SUMMARY, "Stub job complete", {"notes": "Agent scaffolding"})
        storage.mark_status(job_id, JobStatus.COMPLETED)

    def _should_cancel(self, job_id: str) -> bool:
        job = storage.get_job(job_id)
        return bool(job and job.cancel_requested)


runner = AgentRunner()

