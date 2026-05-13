"""
FastAPI dependencies: сессия БД, текущий пользователь, проверка прав.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from backend.api.auth import validate_init_data
from backend.config import settings
from backend.database import crud
from backend.database.models import User, Workspace
from backend.database.session import async_session_factory


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        async with session.begin():
            yield session


async def get_current_user(
    x_init_data: str = Header(..., alias="X-Init-Data"),
    session: AsyncSession = Depends(get_session),
) -> User:
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


async def get_regular_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операций",
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return current_user


async def get_workspace_id(
    current_user: User = Depends(get_current_user),
) -> int:
    """Возвращает workspace_id текущего пользователя или 403 если нет воркспейса."""
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Сначала создайте рабочее пространство через бота",
        )
    return current_user.workspace_id


async def get_workspace(
    workspace_id: int = Depends(get_workspace_id),
    session: AsyncSession = Depends(get_session),
) -> Workspace:
    ws = await crud.get_workspace(session, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рабочее пространство не найдено")
    return ws
