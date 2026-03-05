from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def now_iso() -> str:
    return datetime.utcnow().strftime(ISO_FORMAT)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class EventType(str, Enum):
    INFO = "info"
    PLAN = "plan"
    STEP = "step"
    DIFF = "diff"
    APPLY = "apply"
    TEST = "test"
    REFLECTION = "reflection"
    ERROR = "error"
    SUMMARY = "summary"


@dataclass(slots=True)
class AgentEvent:
    seq: int
    job_id: str
    type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "job_id": self.job_id,
            "type": self.type,
            "message": self.message,
            "data": self.data,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class AgentJob:
    id: str = field(default_factory=lambda: uuid4().hex)
    goal: str = ""
    test_command: Optional[str] = None
    model: Optional[str] = None
    reflections: int = 0
    timeout_minutes: int = 10
    status: JobStatus = JobStatus.PENDING
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    cancel_requested: bool = False
    project: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "test_command": self.test_command,
            "model": self.model,
            "reflections": self.reflections,
            "timeout_minutes": self.timeout_minutes,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cancel_requested": self.cancel_requested,
            "project": self.project,
        }

    def mark_status(self, status: JobStatus) -> None:
        self.status = status
        self.updated_at = now_iso()

    def request_cancel(self) -> None:
        self.cancel_requested = True
        self.updated_at = now_iso()


@dataclass(slots=True)
class JobStartRequest:
    goal: str
    test_command: Optional[str]
    reflections: int
    timeout_minutes: int
    model: Optional[str]
    project: Optional[str]


@dataclass(slots=True)
class JobStatusResponse:
    job: AgentJob
    events: List[AgentEvent]
    next_cursor: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job": self.job.to_dict(),
            "events": [event.to_dict() for event in self.events],
            "next_cursor": self.next_cursor,
        }

