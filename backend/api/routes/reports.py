"""Сводки и отчёты."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import EXPENSE_TYPES, INCOME_TYPES, User
from backend.services.reports import _period_start

router = APIRouter()


@router.get("/report/{period}")
async def get_report(
    period: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Финансовая сводка за период: today / week / month / all."""
    since = _period_start(period)
    txs = await crud.get_transactions(session, user_id=current_user.id, since=since)

    income = sum(t.amount for t in txs if t.type in INCOME_TYPES)
    expense = sum(t.amount for t in txs if t.type in EXPENSE_TYPES)

    ips = await crud.get_all_ips(session)
    owed_to_me, i_owe = await crud.get_active_debts_for_user(session, current_user.id)

    return {
        "period": period,
        "income": income,
        "expense": expense,
        "user_cash": current_user.cash_balance,
        "ips": [
            {
                "id": ip.id,
                "name": ip.name,
                "bank_balance": ip.bank_balance,
                "cash_balance": ip.cash_balance,
            }
            for ip in ips
        ],
        "total_owed_to_me": sum(d.amount for d in owed_to_me),
        "total_i_owe": sum(d.amount for d in i_owe),
    }
