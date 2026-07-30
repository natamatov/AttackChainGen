from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_current_active_user
from app.db.base import get_db
from app.db.models import GlobalSettings, User, UserRole
from app.schemas.settings import SettingInDB, SettingsUpdateBulk


router = APIRouter()

def check_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут управлять глобальными настройками",
        )
    return current_user

@router.get("/", response_model=List[SettingInDB])
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin),
):
    """
    Получение всех глобальных настроек. Доступно только администраторам.
    """
    stmt = select(GlobalSettings)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/", response_model=List[SettingInDB])
async def update_settings(
    settings_in: SettingsUpdateBulk,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin),
):
    """
    Массовое обновление (создание или изменение) настроек.
    Доступно только администраторам.
    """
    for setting in settings_in.settings:
        stmt = select(GlobalSettings).where(GlobalSettings.key == setting.key)
        res = await db.execute(stmt)
        db_obj = res.scalars().first()

        if db_obj:
            db_obj.value = setting.value
            if setting.description is not None:
                db_obj.description = setting.description
        else:
            db_obj = GlobalSettings(
                key=setting.key,
                value=setting.value,
                description=setting.description or "",
            )
            db.add(db_obj)
            
    await db.commit()
    
    # Return updated list
    stmt = select(GlobalSettings)
    result = await db.execute(stmt)
    return result.scalars().all()
