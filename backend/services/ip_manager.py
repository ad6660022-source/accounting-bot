import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import IP

logger = logging.getLogger(__name__)


async def create_ip(
    session: AsyncSession,
    name: str,
    bank_balance: int = 0,
    cash_balance: int = 0,
    workspace_id: int | None = None,
) -> IP:
    existing = await crud.get_ip_by_name(session, name, workspace_id=workspace_id)
    if existing is not None:
        raise ValueError(f"ИП с именем «{name}» уже существует")

    ip = await crud.create_ip(
        session, name=name,
        bank_balance=bank_balance,
        cash_balance=cash_balance,
        workspace_id=workspace_id,
    )
    logger.info("ИП «%s» создано (Р/С: %d ₽, нал: %d ₽)", name, bank_balance, cash_balance)
    return ip


async def update_ip_balances(
    session: AsyncSession, ip_id: int, bank_balance: int, cash_balance: int
) -> IP:
    ip = await crud.set_ip_balances(session, ip_id, bank_balance, cash_balance)
    logger.info("ИП id=%d: Р/С=%d ₽, нал=%d ₽", ip_id, bank_balance, cash_balance)
    return ip
