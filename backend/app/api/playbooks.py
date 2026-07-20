"""
Playbooks API — CRUD сценариев атак.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.db.models import Playbook, User
from app.schemas.playbook import (
    PlaybookCreate,
    PlaybookOut,
    PlaybookSummary,
    PlaybookUpdate,
    PlaybookValidateResult,
)
from app.workers.playbook_parser import PlaybookParser

router = APIRouter(prefix="/api/playbooks", tags=["playbooks"])


@router.get("/", response_model=list[PlaybookSummary])
async def list_playbooks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Playbook]:
    result = await db.execute(
        select(Playbook).order_by(Playbook.updated_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("/", response_model=PlaybookOut, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    body: PlaybookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Playbook:
    # Валидировать YAML перед сохранением
    try:
        pb = PlaybookParser.from_yaml(body.yaml_content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid playbook YAML: {exc}",
        )

    playbook = Playbook(
        name=body.name or pb.name,
        description=body.description or pb.description,
        mitre_tactics=body.mitre_tactics or pb.mitre_tactics,
        mitre_techniques=body.mitre_techniques or pb.mitre_techniques,
        yaml_content=body.yaml_content,
        is_public=body.is_public,
        created_by=current_user.id,
    )
    db.add(playbook)
    await db.flush()
    await db.refresh(playbook)
    return playbook


@router.get("/templates", response_model=list[str])
async def list_step_templates(
    _: User = Depends(get_current_active_user),
) -> list[str]:
    """Список доступных ECS-шаблонов шагов."""
    from pathlib import Path
    from app.workers.template_engine import TemplateEngine
    tpl_dir = Path(__file__).parent.parent.parent / "templates"
    engine = TemplateEngine(templates_dir=tpl_dir)
    return engine.list_templates()


@router.get("/{playbook_id}", response_model=PlaybookOut)
async def get_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Playbook:
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    pb = result.scalar_one_or_none()
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


@router.put("/{playbook_id}", response_model=PlaybookOut)
async def update_playbook(
    playbook_id: int,
    body: PlaybookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Playbook:
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    pb = result.scalar_one_or_none()
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")

    if body.yaml_content:
        try:
            parsed_pb = PlaybookParser.from_yaml(body.yaml_content)
            # Обновляем поля из распарсенного YAML
            pb.description = parsed_pb.description
            pb.mitre_tactics = parsed_pb.mitre_tactics
            pb.mitre_techniques = parsed_pb.mitre_techniques
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid YAML: {exc}",
            )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(pb, field, value)

    await db.flush()
    await db.refresh(pb)
    return pb


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> None:
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    pb = result.scalar_one_or_none()
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    await db.delete(pb)


@router.post("/{playbook_id}/validate", response_model=PlaybookValidateResult)
async def validate_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PlaybookValidateResult:
    """Валидировать сохранённый сценарий."""
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    pb = result.scalar_one_or_none()
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")

    try:
        parsed = PlaybookParser.from_yaml(pb.yaml_content)
        order = parsed.execution_order()
        return PlaybookValidateResult(
            valid=True,
            steps_count=len(parsed.steps),
            execution_order=[s.id for s in order],
        )
    except Exception as exc:
        return PlaybookValidateResult(
            valid=False,
            errors=[str(exc)],
        )
