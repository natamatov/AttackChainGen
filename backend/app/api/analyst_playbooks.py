"""
Analyst Playbooks API — CRUD аналитических плейбуков для SOC-аналитиков.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.db.models import AnalystPlaybook, Playbook, User
from app.schemas.analyst_playbook import (
    AnalystPlaybookCreate,
    AnalystPlaybookOut,
    AnalystPlaybookSummary,
    AnalystPlaybookUpdate,
)

router = APIRouter(prefix="/api/analyst-playbooks", tags=["analyst-playbooks"])


def _enrich(ap: AnalystPlaybook) -> AnalystPlaybookOut:
    """Добавить имя связанного плейбука атаки."""
    out = AnalystPlaybookOut.model_validate(ap)
    if ap.playbook:
        out.playbook_name = ap.playbook.name
    return out


@router.get("/", response_model=list[AnalystPlaybookSummary])
async def list_analyst_playbooks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AnalystPlaybook)
        .options(selectinload(AnalystPlaybook.playbook))
        .order_by(AnalystPlaybook.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = list(result.scalars().all())
    out = []
    for ap in items:
        s = AnalystPlaybookSummary.model_validate(ap)
        if ap.playbook:
            s.playbook_name = ap.playbook.name
        out.append(s)
    return out


@router.get("/{ap_id}", response_model=AnalystPlaybookOut)
async def get_analyst_playbook(
    ap_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AnalystPlaybook)
        .options(selectinload(AnalystPlaybook.playbook))
        .where(AnalystPlaybook.id == ap_id)
    )
    ap = result.scalars().first()
    if not ap:
        raise HTTPException(status_code=404, detail="Analyst playbook not found")
    return _enrich(ap)


@router.post("/", response_model=AnalystPlaybookOut, status_code=status.HTTP_201_CREATED)
async def create_analyst_playbook(
    body: AnalystPlaybookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ap = AnalystPlaybook(
        name=body.name,
        description=body.description,
        playbook_id=body.playbook_id,
        analyst_guide=body.analyst_guide,
        investigation_checklist=body.investigation_checklist,
        created_by=current_user.id,
    )
    db.add(ap)
    await db.commit()
    await db.refresh(ap)

    # Загружаем связанный плейбук для ответа
    if ap.playbook_id:
        pb = await db.get(Playbook, ap.playbook_id)
        ap.playbook = pb

    return _enrich(ap)


@router.patch("/{ap_id}", response_model=AnalystPlaybookOut)
async def update_analyst_playbook(
    ap_id: int,
    body: AnalystPlaybookUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AnalystPlaybook)
        .options(selectinload(AnalystPlaybook.playbook))
        .where(AnalystPlaybook.id == ap_id)
    )
    ap = result.scalars().first()
    if not ap:
        raise HTTPException(status_code=404, detail="Analyst playbook not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ap, field, value)

    await db.commit()
    await db.refresh(ap)

    if ap.playbook_id:
        pb = await db.get(Playbook, ap.playbook_id)
        ap.playbook = pb

    return _enrich(ap)


@router.delete("/{ap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analyst_playbook(
    ap_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    ap = await db.get(AnalystPlaybook, ap_id)
    if not ap:
        raise HTTPException(status_code=404, detail="Analyst playbook not found")
    await db.delete(ap)
    await db.commit()
