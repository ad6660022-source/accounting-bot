"""
Асинхронная сессия SQLAlchemy для PostgreSQL.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings
from backend.database.models import Base

logger = logging.getLogger(__name__)

# Асинхронный движок PostgreSQL (asyncpg)
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Создаёт все таблицы и применяет совместимые миграции.
    Безопасно запускается при каждом старте.
    """
    async with engine.begin() as conn:
        # Миграция: добавляем debit_balance если колонки нет (PostgreSQL)
        await conn.execute(text(
            "ALTER TABLE ips ADD COLUMN IF NOT EXISTS debit_balance INTEGER NOT NULL DEFAULT 0"
        ))
        # Создаём все новые таблицы (существующие не трогает)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")
