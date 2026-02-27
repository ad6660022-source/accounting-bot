"""
Middleware для:
1. DbSessionMiddleware — прокидывает AsyncSession во все хэндлеры
2. UserMiddleware — авторегистрация пользователя и передача db_user
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from backend.config import settings
from backend.database import crud
from backend.database.session import async_session_factory

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """
    Открывает AsyncSession перед каждым апдейтом и закрывает после.
    Сессия доступна в хэндлерах как параметр `session: AsyncSession`.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    """
    Авторегистрация пользователя при первом обращении.
    db_user (объект User из БД) доступен в хэндлерах как параметр.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        session = data.get("session")

        if tg_user and session:
            try:
                async with session.begin():
                    db_user = await crud.get_or_create_user(
                        session,
                        user_id=tg_user.id,
                        username=tg_user.username,
                        admin_ids=settings.admin_ids_list,
                    )
                data["db_user"] = db_user
            except Exception as exc:
                logger.error("UserMiddleware error: %s", exc)
                data["db_user"] = None

        return await handler(event, data)
