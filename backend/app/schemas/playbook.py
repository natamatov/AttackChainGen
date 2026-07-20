"""
Pydantic схемы для Playbook (сценариев атак).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class PlaybookCreate(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    mitre_tactics: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    yaml_content: str
    is_public: bool = True


class PlaybookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mitre_tactics: list[str] | None = None
    mitre_techniques: list[str] | None = None
    yaml_content: str | None = None
    is_public: bool | None = None


class PlaybookOut(BaseModel):
    id: int
    name: str
    description: str | None
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    yaml_content: str
    is_public: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlaybookSummary(BaseModel):
    """Краткое описание без yaml_content (для списков)."""
    id: int
    name: str
    description: str | None
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    is_public: bool
    created_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlaybookValidateResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    steps_count: int = 0
    execution_order: list[str] = Field(default_factory=list)
