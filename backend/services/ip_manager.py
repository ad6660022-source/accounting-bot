"""
Управление ИП: создание, просмотр, обновление капитала.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import IP

logger = logging.getLogger(__name__)


async def create_ip(
    session: AsyncSession, name: str, bank_balance: int = 0, cash_balance: int = 0
) -> IP:
    """
    Создаёт новое ИП с начальными остатками на Р/С и в наличке.
    Проверяет, что ИП с таким именем ещё не существует.
    """
    existing = await crud.get_ip_by_name(session, name)
    if existing is not None:
        raise ValueError(f"ИП с именем «{name}» уже существует")

    ip = await crud.create_ip(session, name=name, bank_balance=bank_balance, cash_balance=cash_balance)
    logger.info("ИП «%s» создано (Р/С: %d ₽, нал: %d ₽)", name, bank_balance, cash_balance)
    return ip


async def update_ip_balances(
    session: AsyncSession, ip_id: int, bank_balance: int, cash_balance: int
) -> IP:
    """Устанавливает балансы ИП (корректировка для админа)."""
    ip = await crud.set_ip_balances(session, ip_id, bank_balance, cash_balance)
    logger.info("ИП id=%d: Р/С=%d ₽, нал=%d ₽", ip_id, bank_balance, cash_balance)
    return ip
