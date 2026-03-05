from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class AutomationState(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    TESTING = "testing"
    LIVE = "live"
    PAUSED = "paused"
    RETIRED = "retired"


class Automation(SQLModel, table=True):
    __tablename__ = "automations"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    state: AutomationState = Field(default=AutomationState.DRAFT)
    version: int = Field(default=1)
    config_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    owner: User = Relationship(back_populates="automations")
    runs: list["AutomationRun"] = Relationship(back_populates="automation")


class AutomationRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AutomationRun(SQLModel, table=True):
    __tablename__ = "automation_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    automation_id: int = Field(foreign_key="automations.id", index=True)
    triggered_by: Optional[int] = Field(default=None, foreign_key="users.id")
    status: AutomationRunStatus = Field(default=AutomationRunStatus.PENDING)
    scheduled_for: Optional[datetime] = Field(default=None, index=True)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    output_json: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    automation: Automation = Relationship(back_populates="runs")
