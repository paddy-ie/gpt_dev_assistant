from datetime import datetime
from typing import Iterable, Optional

from sqlmodel import Session, select

from app.models.automation import Automation, AutomationState


class AutomationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, owner_id: int, name: str, description: str, config_json: str) -> Automation:
        automation = Automation(
            owner_id=owner_id,
            name=name,
            description=description,
            config_json=config_json,
            state=AutomationState.DRAFT,
        )
        self.session.add(automation)
        self.session.commit()
        self.session.refresh(automation)
        return automation

    def list(self, owner_id: Optional[int] = None) -> Iterable[Automation]:
        statement = select(Automation).order_by(Automation.updated_at.desc())
        if owner_id is not None:
            statement = statement.where(Automation.owner_id == owner_id)
        return self.session.exec(statement).all()

    def get(self, automation_id: int) -> Optional[Automation]:
        return self.session.get(Automation, automation_id)

    def update_state(self, automation: Automation, *, state: AutomationState) -> Automation:
        automation.state = state
        automation.version += 1
        automation.updated_at = datetime.utcnow()
        self.session.add(automation)
        self.session.commit()
        self.session.refresh(automation)
        return automation

    def update_config(
        self,
        automation: Automation,
        *,
        description: Optional[str],
        config_json: Optional[str],
    ) -> Automation:
        if description is not None:
            automation.description = description
        if config_json is not None:
            automation.config_json = config_json
        automation.version += 1
        automation.updated_at = datetime.utcnow()
        self.session.add(automation)
        self.session.commit()
        self.session.refresh(automation)
        return automation
