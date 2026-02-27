"""
Публичный список пользователей — для выбора получателя при займе.
Возвращает только id и display_name (без балансов и ролей).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import User

router = APIRouter()


@router.get("/users")
async def list_users_public(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    """Список всех пользователей (только имена) — доступен всем."""
    users = await crud.get_all_users(session)
    return [
        {"id": u.id, "display_name": u.display_name}
        for u in users
        if u.id != current_user.id  # себя исключаем
    ]
