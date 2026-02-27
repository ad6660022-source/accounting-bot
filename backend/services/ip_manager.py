"""
Управление ИП: создание, просмотр, обновление капитала.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import IP

logger = logging.getLogger(__name__)


async def create_ip(session: AsyncSession, name: str, initial_capital: int) -> IP:
    """
    Создаёт новое ИП и зачисляет начальный капитал на расчётный счёт.
    Проверяет, что ИП с таким именем ещё не существует.
    """
    existing = await crud.get_ip_by_name(session, name)
    if existing is not None:
        raise ValueError(f"ИП с именем «{name}» уже существует")

    ip = await crud.create_ip(session, name=name, initial_capital=initial_capital)
    logger.info("ИП «%s» создано, начальный капитал: %d ₽", name, initial_capital)
    return ip


async def set_initial_capital(
    session: AsyncSession, ip_id: int, amount: int
) -> IP:
    """
    Устанавливает начальный капитал ИП (только для админа).
    Обновляет bank_balance и initial_capital.
    """
    ip = await crud.get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.initial_capital = amount
    ip.bank_balance = amount
    logger.info("ИП «%s»: установлен капитал %d ₽", ip.name, amount)
    return ip
