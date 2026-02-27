"""
Точка входа: запускает Telegram-бот и FastAPI-сервер параллельно.
"""

import asyncio
import logging
import os

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from backend.api.app import app as fastapi_app
from backend.bot.handlers import router
from backend.bot.middleware import DbSessionMiddleware, UserMiddleware
from backend.config import settings
from backend.database.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    """Регистрирует команды бота в Telegram (видны в меню команд)."""
    commands = [
        BotCommand(command="start", description="Открыть бухгалтерию"),
        BotCommand(command="help",  description="Справка"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def run_bot() -> None:
    """Запускает Telegram-бот с long polling."""
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await setup_bot_commands(bot)

    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    dp.include_router(router)

    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


async def run_api() -> None:
    """Запускает FastAPI-сервер через uvicorn."""
    port = int(os.environ.get("PORT", settings.port))
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        loop="none",  # используем уже запущенный event loop asyncio
    )
    server = uvicorn.Server(config)
    logger.info("API-сервер запущен на порту %d", port)
    await server.serve()


async def main() -> None:
    logger.info("Запуск бота-бухгалтера...")
    await init_db()
    # Бот и API работают параллельно в одном event loop
    await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    asyncio.run(main())
