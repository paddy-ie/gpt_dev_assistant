from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from utils.paths import WORKSPACE_ROOT

from models import AgentEvent, AgentJob, EventType, JobStartRequest, JobStatus, now_iso

AGENT_ROOT = (WORKSPACE_ROOT / ".agent_jobs").resolve()
AGENT_ROOT.mkdir(parents=True, exist_ok=True)


class AgentStorage:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, AgentJob] = {}
        self._events: Dict[str, List[AgentEvent]] = {}
        self._seq: Dict[str, int] = {}
        self._load_existing()

    # ----------------------------
    # Persistence helpers
    # ----------------------------
    def _job_path(self, job_id: str) -> Path:
        return AGENT_ROOT / f"{job_id}.json"

    def _load_existing(self) -> None:
        for path in AGENT_ROOT.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            job_data = data.get("job")
            events_data = data.get("events", [])
            if not job_data:
                continue
            job = AgentJob(
                id=job_data.get("id", path.stem),
                goal=job_data.get("goal", ""),
                test_command=job_data.get("test_command"),
                model=job_data.get("model"),
                reflections=job_data.get("reflections", 0),
                timeout_minutes=job_data.get("timeout_minutes", 10),
                status=JobStatus(job_data.get("status", JobStatus.PENDING.value)),
                created_at=job_data.get("created_at", now_iso()),
                updated_at=job_data.get("updated_at", now_iso()),
                cancel_requested=job_data.get("cancel_requested", False),
                project=job_data.get("project"),
            )
            events: List[AgentEvent] = []
            for event_data in events_data:
                try:
                    events.append(
                        AgentEvent(
                            seq=int(event_data.get("seq", len(events) + 1)),
                            job_id=job.id,
                            type=str(event_data.get("type", EventType.INFO.value)),
                            message=str(event_data.get("message", "")),
                            data=event_data.get("data", {}),
                            created_at=event_data.get("created_at", now_iso()),
                        )
                    )
                except Exception:
                    continue
            self._jobs[job.id] = job
            self._events[job.id] = events
            self._seq[job.id] = events[-1].seq if events else 0

    def _persist(self, job_id: str) -> None:
        job = self._jobs[job_id]
        events = self._events.get(job_id, [])
        data = {
            "job": job.to_dict(),
            "events": [event.to_dict() for event in events],
        }
        self._job_path(job_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ----------------------------
    # Public API
    # ----------------------------
    def create_job(self, payload: JobStartRequest) -> AgentJob:
        job = AgentJob(
            goal=payload.goal,
            test_command=payload.test_command,
            model=payload.model,
            reflections=payload.reflections,
            timeout_minutes=payload.timeout_minutes,
            project=payload.project,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._events[job.id] = []
            self._seq[job.id] = 0
            self._persist(job.id)
        return job

    def get_job(self, job_id: str) -> Optional[AgentJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            return job

    def list_jobs(self) -> List[AgentJob]:
        with self._lock:
            return list(self._jobs.values())

    def update_job(self, job: AgentJob) -> None:
        with self._lock:
            if job.id not in self._jobs:
                self._jobs[job.id] = job
                self._events.setdefault(job.id, [])
                self._seq.setdefault(job.id, 0)
            else:
                self._jobs[job.id] = job
            self._persist(job.id)

    def append_event(self, job_id: str, event_type: EventType | str, message: str, data: Optional[Dict] = None) -> AgentEvent:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Unknown job {job_id}")
            seq = self._seq.get(job_id, 0) + 1
            self._seq[job_id] = seq
            event = AgentEvent(
                seq=seq,
                job_id=job_id,
                type=str(event_type),
                message=message,
                data=data or {},
            )
            self._events.setdefault(job_id, []).append(event)
            self._persist(job_id)
            return event

    def list_events(self, job_id: str, cursor: Optional[int] = None) -> List[AgentEvent]:
        with self._lock:
            events = self._events.get(job_id, [])
            if cursor is None:
                return list(events)
            return [event for event in events if event.seq > cursor]

    def request_cancel(self, job_id: str) -> Optional[AgentJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.request_cancel()
            self._persist(job_id)
            return job

    def mark_status(self, job_id: str, status: JobStatus) -> Optional[AgentJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.mark_status(status)
            self._persist(job_id)
            return job

    def clear_all(self) -> None:
        with self._lock:
            self._jobs.clear()
            self._events.clear()
            self._seq.clear()
            for path in AGENT_ROOT.glob("*.json"):
                try:
                    path.unlink()
                except OSError:
                    pass


storage = AgentStorage()

