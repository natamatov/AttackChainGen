"""
Stands API — управление стендами Elasticsearch.
Admin может создавать/удалять, инструкторы — только читать.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_admin
from app.db.models import Stand, User
from app.schemas.stand import StandCreate, StandOut, StandTestResult, StandUpdate
from app.workers.elastic_exporter import ElasticExporter

router = APIRouter(prefix="/api/stands", tags=["stands"])


@router.get("/", response_model=list[StandOut])
async def list_stands(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Stand]:
    result = await db.execute(
        select(Stand).where(Stand.is_active == True).order_by(Stand.name)
    )
    return list(result.scalars().all())


@router.post("/", response_model=StandOut, status_code=status.HTTP_201_CREATED)
async def create_stand(
    body: StandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Stand:
    stand = Stand(
        **body.model_dump(),
        created_by=current_user.id,
    )
    db.add(stand)
    await db.flush()
    await db.refresh(stand)
    return stand


@router.get("/{stand_id}", response_model=StandOut)
async def get_stand(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Stand:
    result = await db.execute(select(Stand).where(Stand.id == stand_id))
    stand = result.scalar_one_or_none()
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    return stand


@router.patch("/{stand_id}", response_model=StandOut)
async def update_stand(
    stand_id: int,
    body: StandUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Stand:
    result = await db.execute(select(Stand).where(Stand.id == stand_id))
    stand = result.scalar_one_or_none()
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(stand, field, value)
    await db.flush()
    await db.refresh(stand)
    return stand


@router.delete("/{stand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stand(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    result = await db.execute(select(Stand).where(Stand.id == stand_id))
    stand = result.scalar_one_or_none()
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    # Мягкое удаление
    stand.is_active = False
    await db.flush()


@router.post("/test", response_model=StandTestResult)
async def test_stand_connection_before_create(
    body: StandCreate,
    _: User = Depends(get_current_active_user),
) -> StandTestResult:
    """Проверить соединение с Elasticsearch до сохранения."""
    try:
        exporter = ElasticExporter(
            elastic_url=body.elastic_url,
            api_key=body.api_key,
            username=body.username,
            password=body.password,
            tenant_id=body.tenant_id,
            index=body.index_pattern,
            verify_ssl=body.verify_ssl,
        )
        info = exporter._client.info()
        exporter.close()
        return StandTestResult(
            connected=True,
            message="Connection successful",
            cluster_name=info.get("cluster_name"),
            version=info.get("version", {}).get("number"),
        )
    except Exception as exc:
        return StandTestResult(
            connected=False,
            message=f"Connection failed: {exc}",
        )


@router.post("/{stand_id}/test", response_model=StandTestResult)
async def test_stand_connection(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> StandTestResult:
    """Проверить соединение с Elasticsearch стендом."""
    result = await db.execute(select(Stand).where(Stand.id == stand_id))
    stand = result.scalar_one_or_none()
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")

    try:
        exporter = ElasticExporter(
            elastic_url=stand.elastic_url,
            api_key=stand.api_key,
            username=stand.username,
            password=stand.password,
            tenant_id=stand.tenant_id,
            index=stand.index_pattern,
            verify_ssl=stand.verify_ssl,
        )
        info = exporter._client.info()
        exporter.close()
        return StandTestResult(
            connected=True,
            message="Connection successful",
            cluster_name=info.get("cluster_name"),
            version=info.get("version", {}).get("number"),
        )
    except Exception as exc:
        return StandTestResult(
            connected=False,
            message=f"Connection failed: {exc}",
        )
