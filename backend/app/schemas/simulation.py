"""
Pydantic схемы для SimulationRun (запуски симуляций).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.db.models import SimulationStatus, SimulationMode, NoiseLevel


class SimulationRunCreate(BaseModel):
    playbook_id: int
    stand_id: int
    mode: SimulationMode = SimulationMode.REALTIME
    noise_level: NoiseLevel = NoiseLevel.NONE
    backdate_offset: str | None = Field(
        default=None,
        description="Для historical режима: '3d', '12h', '2026-07-01T10:00:00'"
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Переопределение переменных: {'user.name': 'admin'}"
    )


class SimulationRunOut(BaseModel):
    id: int
    playbook_id: int | None
    stand_id: int | None
    created_by: int | None
    status: SimulationStatus
    mode: SimulationMode
    noise_level: NoiseLevel
    backdate_offset: str | None
    overrides: dict | None
    celery_task_id: str | None
    progress_current: int
    progress_total: int
    progress_message: str | None
    artifacts: dict | None
    events_sent: int
    error_message: str | None
    playbook_name: str | None
    stand_name: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationRunSummary(BaseModel):
    """Краткое описание для списков."""
    id: int
    playbook_name: str | None
    stand_name: str | None
    status: SimulationStatus
    mode: SimulationMode
    noise_level: NoiseLevel
    progress_current: int
    progress_total: int
    events_sent: int
    created_by: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationProgressUpdate(BaseModel):
    """WebSocket / polling сообщение о прогрессе."""
    run_id: int
    status: SimulationStatus
    progress_current: int
    progress_total: int
    progress_message: str | None
    events_sent: int


class SimulationAccepted(BaseModel):
    """Ответ на POST /simulations/run."""
    status: str = "accepted"
    run_id: int
    message: str = "Simulation queued successfully"
