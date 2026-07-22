"""
Pydantic схемы для AnalystPlaybook.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class AnalystPlaybookCreate(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    playbook_id: int | None = None
    analyst_guide: str | None = None
    investigation_checklist: str | None = None


class AnalystPlaybookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    playbook_id: int | None = None
    analyst_guide: str | None = None
    investigation_checklist: str | None = None


class AnalystPlaybookOut(BaseModel):
    id: int
    name: str
    description: str | None
    playbook_id: int | None
    analyst_guide: str | None
    investigation_checklist: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    playbook_name: str | None = None

    model_config = {"from_attributes": True}


class AnalystPlaybookSummary(BaseModel):
    id: int
    name: str
    description: str | None
    playbook_id: int | None
    playbook_name: str | None = None
    analyst_guide: str | None = None
    investigation_checklist: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
