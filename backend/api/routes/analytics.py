"""
Эндпоинт аналитики оборота по типам операций.
Поддерживает фильтрацию по ИП и периоду.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import TxType, User
from backend.services.reports import _period_start

router = APIRouter()

_INCOME_TYPES = {TxType.PRIHOD_MES, TxType.PRIHOD_FAST, TxType.PRIHOD_STO}
_EXPENSE_TYPES = {TxType.ZAKUP, TxType.STORONNIE, TxType.EXPENSE_WRITEOFF}


@router.get("/analytics")
async def get_analytics(
    period: str = "all",
    ip_id: Optional[int] = None,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    since = _period_start(period)
    txs = await crud.get_transactions(session, ip_id=ip_id, since=since, limit=10000)

    by_type: dict[str, int] = {}
    for tx in txs:
        by_type[tx.type] = by_type.get(tx.type, 0) + tx.amount

    total_income = sum(by_type.get(t, 0) for t in _INCOME_TYPES)
    total_expense = sum(by_type.get(t, 0) for t in _EXPENSE_TYPES)

    return {
        "period": period,
        "ip_id": ip_id,
        "by_type": by_type,
        "total_income": total_income,
        "total_expense": total_expense,
    }
