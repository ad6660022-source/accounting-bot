"""
Асинхронная сессия SQLAlchemy для PostgreSQL.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings
from backend.database.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_MIGRATIONS = [
    # Старые колонки
    "ALTER TABLE ips ADD COLUMN IF NOT EXISTS debit_balance INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS destination VARCHAR(20)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS expense_id INTEGER",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS cancelled_by_id BIGINT",
    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS is_closed BOOLEAN NOT NULL DEFAULT FALSE",
    # Мультитенантность
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "ALTER TABLE ips ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "ALTER TABLE ip_debts ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    # Убираем старый уникальный индекс на имя ИП (если был)
    "DROP INDEX IF EXISTS ix_ips_name",
    "ALTER TABLE ips DROP CONSTRAINT IF EXISTS ips_name_key",
]


async def init_db() -> None:
    async with engine.begin() as conn:
        for sql in _MIGRATIONS:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                logger.debug("Migration skipped (%s): %s", sql[:60], e)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")
