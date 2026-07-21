from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.db.models import FictionalEnvironment, NetworkZone, Asset
from app.schemas.environments import (
    FictionalEnvironmentCreate,
    FictionalEnvironmentUpdate,
    FictionalEnvironmentOut,
    NetworkZoneCreate,
    NetworkZoneUpdate,
    NetworkZoneOut,
    AssetCreate,
    AssetUpdate,
    AssetOut,
)

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────── #
# Environments
# ─────────────────────────────────────────────────────────────────────── #

@router.get("/", response_model=list[FictionalEnvironmentOut])
async def list_environments(db: AsyncSession = Depends(get_db)):
    stmt = select(FictionalEnvironment).options(
        selectinload(FictionalEnvironment.zones).selectinload(NetworkZone.assets)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/", response_model=FictionalEnvironmentOut, status_code=status.HTTP_201_CREATED)
async def create_environment(
    env_in: FictionalEnvironmentCreate,
    db: AsyncSession = Depends(get_db)
):
    env = FictionalEnvironment(**env_in.model_dump())
    db.add(env)
    await db.commit()
    await db.refresh(env)
    # Reload with relations
    stmt = select(FictionalEnvironment).options(
        selectinload(FictionalEnvironment.zones).selectinload(NetworkZone.assets)
    ).where(FictionalEnvironment.id == env.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.get("/{env_id}", response_model=FictionalEnvironmentOut)
async def get_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(FictionalEnvironment).options(
        selectinload(FictionalEnvironment.zones).selectinload(NetworkZone.assets)
    ).where(FictionalEnvironment.id == env_id)
    res = await db.execute(stmt)
    env = res.scalars().first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.put("/{env_id}", response_model=FictionalEnvironmentOut)
async def update_environment(
    env_id: int,
    env_in: FictionalEnvironmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    env = await get_environment(env_id, db)
    update_data = env_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(env, k, v)
    await db.commit()
    return await get_environment(env_id, db)


@router.delete("/{env_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    env = await db.get(FictionalEnvironment, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    await db.delete(env)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────── #
# Network Zones
# ─────────────────────────────────────────────────────────────────────── #

@router.post("/{env_id}/zones", response_model=NetworkZoneOut, status_code=status.HTTP_201_CREATED)
async def create_zone(
    env_id: int,
    zone_in: NetworkZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    env = await db.get(FictionalEnvironment, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    zone = NetworkZone(**zone_in.model_dump(), environment_id=env_id)
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone

@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    zone = await db.get(NetworkZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    await db.delete(zone)
    await db.commit()

# ─────────────────────────────────────────────────────────────────────── #
# Assets
# ─────────────────────────────────────────────────────────────────────── #

@router.post("/zones/{zone_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def create_asset(
    zone_id: int,
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    zone = await db.get(NetworkZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    asset = Asset(**asset_in.model_dump(), zone_id=zone_id)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset

@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)
    await db.commit()
