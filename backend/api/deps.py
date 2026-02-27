"""
FastAPI dependencies: сессия БД, текущий пользователь, проверка прав.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import validate_init_data
from backend.config import settings
from backend.database import crud
from backend.database.models import User
from backend.database.session import async_session_factory


async def get_session() -> AsyncSession:
    """Dependency: открывает сессию БД и оборачивает запрос в одну транзакцию."""
    async with async_session_factory() as session:
        async with session.begin():
            yield session


async def get_current_user(
    x_init_data: str = Header(..., alias="X-Init-Data"),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Dependency: валидирует Telegram initData и возвращает пользователя из БД.
    Автоматически регистрирует нового пользователя при первом обращении.
    """
    try:
        tg_user = validate_init_data(x_init_data, settings.telegram_bot_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    db_user = await crud.get_or_create_user(
        session,
        user_id=tg_user["id"],
        username=tg_user.get("username"),
        admin_ids=settings.admin_ids_list,
    )
    return db_user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: проверяет что пользователь — администратор."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return current_user
