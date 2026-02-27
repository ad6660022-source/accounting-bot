"""Балансы пользователя и ИП."""

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
    """Возвращает личный баланс и балансы всех ИП."""
    ips = await crud.get_all_ips(session)
    return {
        "user": {
            "cash_balance": current_user.cash_balance,
        },
        "ips": [
            {
                "id": ip.id,
                "name": ip.name,
                "bank_balance": ip.bank_balance,
                "cash_balance": ip.cash_balance,
            }
            for ip in ips
        ],
    }
