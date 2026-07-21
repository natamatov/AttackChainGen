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
    
    stmt = select(NetworkZone).options(selectinload(NetworkZone.assets)).where(NetworkZone.id == zone.id)
    res = await db.execute(stmt)
    return res.scalars().first()

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

import ipaddress

@router.post("/zones/{zone_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def create_asset(
    zone_id: int,
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    zone = await db.get(NetworkZone, zone_id, options=[selectinload(NetworkZone.assets)])
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    if not asset_in.ip_address:
        if "-" in zone.ip_range:
            try:
                start_ip_str, end_ip_str = [x.strip() for x in zone.ip_range.split("-")]
                start_ip = ipaddress.IPv4Address(start_ip_str)
                end_ip = ipaddress.IPv4Address(end_ip_str)
                
                existing_ips = set()
                for a in zone.assets:
                    try:
                        existing_ips.add(ipaddress.IPv4Address(a.ip_address))
                    except:
                        pass
                        
                current_ip = start_ip
                assigned_ip = None
                while current_ip <= end_ip:
                    if current_ip not in existing_ips:
                        assigned_ip = str(current_ip)
                        break
                    current_ip = ipaddress.IPv4Address(int(current_ip) + 1)
                    
                if not assigned_ip:
                    raise HTTPException(status_code=400, detail="No available IP addresses in the given range")
                asset_in.ip_address = assigned_ip
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to auto-generate IP: {e}")
        else:
            raise HTTPException(status_code=400, detail="Zone does not have a valid IP range format (e.g., 10.0.0.10-10.0.0.20)")

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
