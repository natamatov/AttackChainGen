from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session, selectinload
import logging

from app.services.opencti_service import opencti_service
from sqlalchemy.future import select
from app.services.opencti_service import opencti_service
from app.db.base import get_db
from app.db.models import MitreMapping, Playbook, FictionalEnvironment, Asset
from app.schemas.opencti import MitreMappingResponse, MitreMappingCreate, MitreMappingUpdate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/threat-actors")
async def get_threat_actors(limit: int = 200, db: Session = Depends(get_db)):
    """Возвращает список APT-групп (Intrusion Sets) из OpenCTI."""
    try:
        await opencti_service.get_credentials(db)
        actors = opencti_service.get_threat_actors(limit=limit)
        return {"items": actors, "total": len(actors)}
    except Exception as e:
        logger.error(f"Failed to fetch Threat Actors from OpenCTI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenCTI connection error: {str(e)}")

@router.post("/generate-playbook/{actor_id}")
async def generate_playbook(actor_id: str, actor_name: str, domain: str = "corp.local", report_id: str = None, db: Session = Depends(get_db)):
    """Генерирует YAML плейбук на основе техник Threat Actor."""
    try:
        # Fetch mappings asynchronously
        result_mappings = await db.execute(select(MitreMapping))
        db_mappings = result_mappings.scalars().all()
        template_map = {m.mitre_id: m.template_name for m in db_mappings}
        
        if not template_map:
            default_map = {
                "T1566": "win_sysmon_1_process_creation",
                "T1059": "win_sysmon_1_process_creation",
                "T1078": "win_security_4624",
                "T1110": "win_security_4625",
                "T1046": "network_connection",
                "T1021": "win_security_4624",
                "T1486": "sysmon_event_11",
                "T1136": "win_security_4720",
                "T1098": "win_security_4732"
            }
            for k, v in default_map.items():
                new_map = MitreMapping(mitre_id=k, template_name=v)
                db.add(new_map)
            await db.commit()
            template_map = default_map

        # Fetch assets from CMDB for the given domain
        env_result = await db.execute(select(FictionalEnvironment).where(FictionalEnvironment.domain == domain))
        env = env_result.scalars().first()
        
        if not env:
            logger.warning(f"Environment with domain {domain} not found. Falling back to the first available environment.")
            env_result = await db.execute(select(FictionalEnvironment))
            env = env_result.scalars().first()

        assets = []
        if env:
            assets_result = await db.execute(
                select(Asset).options(selectinload(Asset.zone)).join(Asset.zone).where(Asset.zone.has(environment_id=env.id))
            )
            assets = assets_result.scalars().all()
            if not assets:
                logger.warning(f"No assets found in environment {env.name} ({env.domain}).")
        else:
            logger.warning("No environments found in the CMDB.")

        # Use run_in_threadpool if we want to not block, but opencti_service is quick
        await opencti_service.get_credentials(db)
        result = opencti_service.generate_playbook_from_actor(actor_id, actor_name, domain, template_map, assets, report_id)
        return {"playbook": result["yaml"], "guide": result["markdown"], "stix_references": result.get("stix_references")}
    except Exception as e:
        logger.error(f"Failed to generate playbook from OpenCTI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate playbook: {str(e)}")

# --- Mappings CRUD ---

@router.get("/mappings", response_model=List[MitreMappingResponse])
async def get_mappings(db: Session = Depends(get_db)):
    """Получить все динамические маппинги."""
    result = await db.execute(select(MitreMapping))
    return result.scalars().all()

@router.post("/mappings", response_model=MitreMappingResponse)
async def create_mapping(mapping: MitreMappingCreate, db: Session = Depends(get_db)):
    """Создать новый маппинг."""
    res = await db.execute(select(MitreMapping).where(MitreMapping.mitre_id == mapping.mitre_id))
    existing = res.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Mapping for this MITRE ID already exists")
    new_mapping = MitreMapping(**mapping.model_dump())
    db.add(new_mapping)
    await db.commit()
    await db.refresh(new_mapping)
    return new_mapping

@router.put("/mappings/{mapping_id}", response_model=MitreMappingResponse)
async def update_mapping(mapping_id: int, mapping: MitreMappingUpdate, db: Session = Depends(get_db)):
    """Обновить маппинг."""
    res = await db.execute(select(MitreMapping).where(MitreMapping.id == mapping_id))
    db_mapping = res.scalars().first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    update_data = mapping.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mapping, key, value)
    
    await db.commit()
    await db.refresh(db_mapping)
    return db_mapping

@router.delete("/mappings/{mapping_id}")
async def delete_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """Удалить маппинг."""
    res = await db.execute(select(MitreMapping).where(MitreMapping.id == mapping_id))
    db_mapping = res.scalars().first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    await db.delete(db_mapping)
    await db.commit()
    return {"message": "Mapping deleted successfully"}
