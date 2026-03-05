from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class RunStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STALLED = "stalled"


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id")
    repo_label: str = Field(index=True)
    goal: str
    status: RunStatus = Field(default=RunStatus.PENDING)
    token_usage: int = Field(default=0)
    max_runtime_minutes: int = Field(default=200)
    started_at: datetime | None = Field(default=None, index=True)
    finished_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    owner: User = Relationship(back_populates="runs")
    steps: list["RunStep"] = Relationship(back_populates="run")
    events: list["RunEvent"] = Relationship(back_populates="run")


class RunStep(SQLModel, table=True):
    __tablename__ = "run_steps"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="run_steps.id")
    type: str = Field(default="plan", index=True)
    status: RunStatus = Field(default=RunStatus.PENDING)
    summary: str = Field(default="")
    llm_input: Optional[str] = None
    llm_output: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    run: Run = Relationship(back_populates="steps")
    parent: Optional["RunStep"] = Relationship(sa_relationship_kwargs={"remote_side": "RunStep.id"})


class RunEvent(SQLModel, table=True):
    __tablename__ = "run_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", index=True)
    step_id: Optional[int] = Field(default=None, foreign_key="run_steps.id")
    type: str = Field(default="log", index=True)
    level: str = Field(default="info")
    message: str = Field(default="")
    payload_json: Optional[str] = None
    sequence: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    run: Run = Relationship(back_populates="events")
    step: Optional[RunStep] = Relationship(sa_relationship_kwargs={"lazy": "joined"})
