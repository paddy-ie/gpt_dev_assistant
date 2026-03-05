from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.run import RunStatus


class RunBase(BaseModel):
    repo_label: str
    goal: str
    max_runtime_minutes: int = 200


class RunCreate(RunBase):
    pass


class RunUpdate(BaseModel):
    status: Optional[RunStatus] = None
    token_usage: Optional[int] = None
    finished_at: Optional[datetime] = None


class RunRead(RunBase):
    id: int
    owner_id: int
    status: RunStatus
    token_usage: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunEventRead(BaseModel):
    id: int
    run_id: int
    step_id: Optional[int]
    type: str
    level: str
    message: str
    payload_json: Optional[str]
    sequence: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunStepRead(BaseModel):
    id: int
    run_id: int
    parent_id: Optional[int]
    type: str
    status: RunStatus
    summary: str
    llm_input: Optional[str]
    llm_output: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
