"""
Асинхронная сессия SQLAlchemy для PostgreSQL.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings
from backend.database.models import Base

logger = logging.getLogger(__name__)

# Асинхронный движок PostgreSQL (asyncpg)
engine = create_async_engine(
    settings.database_url,
    echo=False,       # True — выводит SQL-запросы в лог (для отладки)
    pool_size=10,
    max_overflow=20,
)

# Фабрика сессий — expire_on_commit=False чтобы объекты были доступны после commit
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Создаёт все таблицы в БД на основе моделей.
    Используется при первом запуске (без Alembic).
    В продакшене таблицы управляются через Alembic-миграции.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")
