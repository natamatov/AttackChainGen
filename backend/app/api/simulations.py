"""
Simulations API — запуск симуляций, история, прогресс, артефакты.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.db.models import Playbook, SimulationRun, SimulationStatus, Stand, User
from app.schemas.simulation import (
    SimulationAccepted,
    SimulationRunCreate,
    SimulationRunOut,
    SimulationRunSummary,
)
from app.workers.tasks import run_simulation

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


@router.post("/run", response_model=SimulationAccepted, status_code=status.HTTP_202_ACCEPTED)
async def start_simulation(
    body: SimulationRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SimulationAccepted:
    """
    Поставить симуляцию в очередь Celery.
    Немедленно возвращает {status: accepted, run_id}.
    """
    # Проверить существование playbook и stand
    pb = await db.get(Playbook, body.playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")

    stand = await db.get(Stand, body.stand_id)
    if not stand or not stand.is_active:
        raise HTTPException(status_code=404, detail="Stand not found or inactive")

    # Создать запись SimulationRun
    run = SimulationRun(
        playbook_id=body.playbook_id,
        stand_id=body.stand_id,
        created_by=current_user.id,
        status=SimulationStatus.PENDING,
        mode=body.mode,
        noise_level=body.noise_level,
        backdate_offset=body.backdate_offset,
        overrides=body.overrides,
        # Снапшоты имён
        playbook_name=pb.name,
        stand_name=stand.name,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    # Отправить задачу в Celery
    task = run_simulation.delay(run.id)
    run.celery_task_id = task.id
    await db.flush()

    return SimulationAccepted(run_id=run.id)


@router.get("/", response_model=list[SimulationRunSummary])
async def list_runs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SimulationRun]:
    """История запусков (текущий пользователь видит свои, admin — все)."""
    from app.db.models import UserRole
    query = select(SimulationRun).order_by(desc(SimulationRun.created_at)).offset(skip).limit(limit)
    if current_user.role != UserRole.ADMIN:
        query = query.where(SimulationRun.created_by == current_user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{run_id}", response_model=SimulationRunOut)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> SimulationRun:
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


@router.post("/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Отменить запущенную симуляцию."""
    from app.core.config import get_settings
    import redis.asyncio as aioredis

    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in (SimulationStatus.PENDING, SimulationStatus.RUNNING):
        raise HTTPException(status_code=400, detail=f"Cannot cancel run in status '{run.status}'")

    # Установить флаг отмены в Redis
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url)
    await r.set(f"cancel:{run_id}", "1", ex=3600)
    await r.aclose()

    return {"status": "cancellation_requested", "run_id": run_id}


@router.get("/{run_id}/artifacts")
async def get_artifacts(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    """Получить артефакты (IoC шпаргалку) завершённой симуляции."""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Artifacts available only for completed runs (current: {run.status})"
        )
    return {
        "run_id": run_id,
        "playbook_name": run.playbook_name,
        "events_sent": run.events_sent,
        "artifacts": run.artifacts or {},
    }

@router.get("/last-error/debug")
async def get_last_error(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimulationRun.error_message).order_by(SimulationRun.id.desc()).limit(1))
    return {"error": result.scalar()}
