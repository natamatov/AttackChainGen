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
        
    # Сбор шаблонов — используем абсолютный путь как в tasks.py
    from pathlib import Path as _Path
    templates_dir_path = _Path(__file__).parent.parent.parent.parent / "templates"
    templates_dir = str(templates_dir_path)
    templates = []
    if templates_dir_path.exists():
        for f in templates_dir_path.glob("*.json.j2"):
            templates.append(f.name.replace(".json.j2", ""))
                
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
В полях source_ip, host_name, destination_ip и других IP/именах используй СТРОГО данные из предоставленного выше списка!

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА YAML (соблюдай точно):
name: "Название сценария"
description: "Описание"
global_context:
  host.name: "HOSTNAME"     # Хост-жертва из списка выше
  host.domain: "{env.domain}"
  user.name: "username"     # Имя пользователя-жертвы
steps:
  - id: "step_1_initial_access"
    template: "название_шаблона"   # СТРОГО один из доступных шаблонов!
    description: "Подробное описание шага"
    delay_from_prev: "0s"
    fields:                        # ВСЕ поля шага ОБЯЗАТЕЛЬНО внутри fields:
      host_name: "HOSTNAME"        # Имя хоста из списка выше
      host_ip: "IP_АДРЕС"         # IP из списка выше
      source_ip: "IP_ИСТОЧНИКА"
      destination_ip: "IP_ЦЕЛИ"
      user_name: "username"
      process_name: "process.exe"
      mitre_technique: "T1566.001"

  - id: "step_2_lateral_movement"
    template: "другой_шаблон"
    description: "Описание"
    delay_from_prev: "5m"
    depends_on: "step_1_initial_access"   # Ссылка на предыдущий шаг
    fields:
      host_name: "ДРУГОЙ_ХОСТ"
      host_ip: "ДРУГОЙ_IP"
      source_ip: "IP_ИСТОЧНИКА"

ПРАВИЛА:
1. Поле `template` АБСОЛЮТНО ОБЯЗАТЕЛЬНО в каждом шаге!
2. ВСЕ поля шага должны быть ВНУТРИ блока `fields:` — НЕ в корне шага!
3. Используй СТРОГО имена хостов и IP из списка выше — НЕ выдумывай!
4. Используй СТРОГО имена шаблонов из списка выше — НЕ выдумывай!
5. Раздел global_context ОБЯЗАТЕЛЕН — укажи там основной хост атаки.
"""

    return {"prompt": prompt}

