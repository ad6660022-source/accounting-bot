"""Информация о текущем пользователе."""

from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user
from backend.database.models import User

router = APIRouter()


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "cash_balance": current_user.cash_balance,
    }
