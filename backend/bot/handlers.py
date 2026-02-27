"""
Хэндлеры Telegram-бота.
Бот минимален: регистрация + кнопка открытия Mini App.
Вся бухгалтерия — в Mini App (fastapi_app/frontend).
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import crud
from backend.database.models import User

logger = logging.getLogger(__name__)
router = Router()


# ── Вспомогательная функция ───────────────────────────────────────────────────

def _webapp_keyboard() -> InlineKeyboardMarkup:
    """Кнопка «Открыть Mini App»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть бухгалтерию",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )


# ── /start — регистрация и приветствие ────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User, bot: Bot, session: AsyncSession) -> None:
    """
    Регистрирует пользователя (автоматически) и показывает главную кнопку Mini App.
    Если передан admin-код (/start ACC-ADMIN-2025) — повышает до администратора.
    """
    args = message.text.split(maxsplit=1)
    admin_note = ""

    if len(args) > 1:
        code = args[1].strip()
        if code == settings.admin_invite_code:
            if db_user.role != "admin":
                async with session.begin():
                    await crud.set_user_role(session, db_user.id, "admin")
                db_user.role = "admin"
                admin_note = "\n\n👑 <b>Вы стали администратором!</b>"
            else:
                admin_note = "\n\n👑 Вы уже администратор."
        else:
            admin_note = "\n\n❌ Неверный код."

    name = message.from_user.first_name or "друг"
    role_label = "👑 Администратор" if db_user.role == "admin" else "👤 Пользователь"

    text = (
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Роль: {role_label}\n\n"
        f"Это бот-бухгалтер для учёта финансов ИП.\n"
        f"Все операции выполняются через приложение ниже.{admin_note}"
    )

    # Устанавливаем кнопку меню (постоянная кнопка снизу в Telegram)
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="📱 Бухгалтерия",
                web_app=WebAppInfo(url=settings.webapp_url),
            ),
        )
    except Exception as e:
        logger.warning("Не удалось установить menu button: %s", e)

    await message.answer(text, reply_markup=_webapp_keyboard())


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User) -> None:
    role_label = "👑 Администратор" if db_user.role == "admin" else "👤 Пользователь"
    await message.answer(
        f"ℹ️ <b>Справка</b>\n\n"
        f"Ваша роль: {role_label}\n\n"
        f"<b>Команды:</b>\n"
        f"/start — приветствие и кнопка открытия приложения\n"
        f"/help — эта справка\n\n"
        f"<b>Получить права администратора:</b>\n"
        f"Отправь боту: <code>/start КОД_АДМИНИСТРАТОРА</code>\n\n"
        f"Все операции (закуп, приход, долги, сводки) — в Mini App:",
        reply_markup=_webapp_keyboard(),
    )


# ── Обработка неизвестных сообщений ──────────────────────────────────────────

@router.message(F.text)
async def unknown_message(message: Message) -> None:
    await message.answer(
        "Используй кнопку ниже для открытия приложения 👇",
        reply_markup=_webapp_keyboard(),
    )
