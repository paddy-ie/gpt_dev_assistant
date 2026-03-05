from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.automation import AutomationRunStatus, AutomationState


class AutomationBase(BaseModel):
    name: str
    description: str = ""
    config_json: str = "{}"


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    state: Optional[AutomationState] = None
    description: Optional[str] = None
    config_json: Optional[str] = None


class AutomationRead(AutomationBase):
    id: int
    owner_id: int
    state: AutomationState
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutomationRunCreate(BaseModel):
    scheduled_for: Optional[datetime] = None


class AutomationRunRead(BaseModel):
    id: int
    automation_id: int
    triggered_by: Optional[int]
    status: AutomationRunStatus
    scheduled_for: Optional[datetime]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    output_json: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
