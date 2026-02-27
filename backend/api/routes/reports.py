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
    since = _period_start(period)
    txs = await crud.get_transactions(session, user_id=current_user.id, since=since)

    income = sum(t.amount for t in txs if t.type in INCOME_TYPES)
    expense = sum(t.amount for t in txs if t.type in EXPENSE_TYPES)

    ips = await crud.get_all_ips(session)
    ip_debts = await crud.get_active_ip_debts(session)

    return {
        "period": period,
        "income": income,
        "expense": expense,
        "ips": [
            {
                "id": ip.id,
                "name": ip.name,
                "bank_balance": ip.bank_balance,
                "debit_balance": ip.debit_balance,
                "cash_balance": ip.cash_balance,
            }
            for ip in ips
        ],
        "ip_debts": [
            {
                "debtor_ip_name": d.debtor_ip.name,
                "creditor_ip_name": d.creditor_ip.name,
                "amount": d.amount,
            }
            for d in ip_debts
        ],
    }
