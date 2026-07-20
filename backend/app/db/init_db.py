"""
Скрипт для инициализации базы данных (создание первого админа).
Запускается вручную: python -m app.db.init_db
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import AsyncSessionLocal
from app.db.models import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def init_db() -> None:
    async with AsyncSessionLocal() as session:
        # Проверяем, есть ли уже админ
        result = await session.execute(
            select(User).where(User.email == settings.first_superuser)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.info("Creating first superuser...")
            admin_user = User(
                email=settings.first_superuser,
                hashed_password=get_password_hash(settings.first_superuser_password),
                full_name="System Admin",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Superuser {settings.first_superuser} created successfully!")
        else:
            logger.info("Superuser already exists.")


async def main() -> None:
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
