from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.db.models import FictionalEnvironment, NetworkZone
import os
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/{env_id}")
async def generate_prompt(env_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(FictionalEnvironment).options(
        selectinload(FictionalEnvironment.zones).selectinload(NetworkZone.assets)
    ).where(FictionalEnvironment.id == env_id)
    res = await db.execute(stmt)
    env = res.scalars().first()
    
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
        
    # Сбор шаблонов
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
    templates = []
    if os.path.exists(templates_dir):
        for f in os.listdir(templates_dir):
            if f.endswith(".json.j2"):
                templates.append(f.replace(".json.j2", ""))
                
    # Формирование промпта
    prompt = f"""Ты эксперт по Red Teaming и созданию контента для SIEM (Cyber Range / BAS). 
Напиши YAML-плейбук для симулятора AttackChainGen. 

ОГРАНИЧЕНИЯ ИНФРАСТРУКТУРЫ (Используй ТОЛЬКО эти данные):
Домен: {env.domain}

"""
    for zone in env.zones:
        prompt += f"Сетевой сегмент: {zone.name} (Диапазон IP: {zone.ip_range})\n"
        if zone.assets:
            for asset in zone.assets:
                role_str = f" - {asset.role}" if asset.role else ""
                prompt += f"- {asset.hostname} ({asset.ip_address}){role_str}\n"
        else:
            prompt += "- (Нет заданных хостов. Ты можешь использовать любые IP-адреса из указанного диапазона этого сегмента)\n"
        prompt += "\n"
        
    prompt += f"ДОСТУПНЫЕ ШАБЛОНЫ СОБЫТИЙ:\n- {', '.join(templates) if templates else 'Нет шаблонов'}\n\n"
    
    prompt += """ЗАДАЧА:
Напиши сценарий атаки, логически выстраивая шаги (Initial Access -> Recon -> Lateral Movement).
В полях source_ip, host.ip и других IP-адресах используй строго IP-адреса из предоставленного выше списка или пула.

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА YAML:
playbook:
  name: "Название сценария"
  description: "Описание"
  steps:
    - id: "step_1"
      template: "название_шаблона" # СТРОГО один из доступных шаблонов событий, указанных выше! (без .json.j2)
      description: "Подробное описание шага"
      delay_from_prev: "0s" # Задержка от предыдущего шага, например "5s", "1m"
      # Любые другие поля (host.ip, user.name, mitre_technique и т.д.) указывай здесь же в корне шага.

ВНИМАНИЕ: поле `template` в каждом шаге АБСОЛЮТНО ОБЯЗАТЕЛЬНО! Без него сценарий не будет работать. Выбирай только из предоставленного списка доступных шаблонов.
"""

    return {"prompt": prompt}
