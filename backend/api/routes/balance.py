from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import User

router = APIRouter()


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ips = await crud.get_all_ips(session)
    ip_list = [
        {
            "id": ip.id,
            "name": ip.name,
            "bank_balance": ip.bank_balance,
            "debit_balance": ip.debit_balance,
            "cash_balance": ip.cash_balance,
        }
        for ip in ips
    ]
    total_bank = sum(ip.bank_balance for ip in ips)
    total_debit = sum(ip.debit_balance for ip in ips)
    total_cash = sum(ip.cash_balance for ip in ips)
    return {
        "total_bank": total_bank,
        "total_debit": total_debit,
        "total_cash": total_cash,
        "ips": ip_list,
    }
