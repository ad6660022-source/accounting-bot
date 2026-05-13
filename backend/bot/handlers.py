"""
Хэндлеры Telegram-бота.
Регистрация, воркспейс-онбординг, подписка, кнопка Mini App.
"""

import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    MenuButtonWebApp,
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    WebAppInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.bot.states import WorkspaceStates
from backend.config import settings
from backend.database import crud
from backend.database.models import PLAN_LIMITS, User

logger = logging.getLogger(__name__)
router = Router()


# ── Клавиатуры ───────────────────────────────────────────────────────────────

def _webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📱 Открыть бухгалтерию",
            web_app=WebAppInfo(url=settings.webapp_url),
        )
    ]])


def _onboarding_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Создать пространство", callback_data="ws_create")],
        [InlineKeyboardButton(text="🔑 Войти по коду", callback_data="ws_join")],
    ])


def _subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ Pro — {settings.pro_price_stars} ⭐/мес (~{settings.pro_price_stars * 1.82:.0f} руб)",
            callback_data="sub_pro",
        )],
        [InlineKeyboardButton(
            text=f"💎 Business — {settings.business_price_stars} ⭐/мес (~{settings.business_price_stars * 1.82:.0f} руб)",
            callback_data="sub_business",
        )],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="sub_cancel")],
    ])


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User, bot: Bot, session: AsyncSession) -> None:
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

    if not db_user.workspace_id:
        await message.answer(
            f"👋 Привет, <b>{name}</b>!\n\n"
            f"Добро пожаловать в <b>Бухгалтер ИП</b>.\n\n"
            f"Для начала работы создайте рабочее пространство "
            f"или присоединитесь к существующему по коду:{admin_note}",
            reply_markup=_onboarding_keyboard(),
        )
        return

    role_label = "👑 Администратор" if db_user.role == "admin" else "👤 Пользователь"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Роль: {role_label}\n\n"
        f"Используй кнопку ниже для работы с бухгалтерией.{admin_note}",
        reply_markup=_webapp_keyboard(),
    )


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User) -> None:
    role_label = "👑 Администратор" if db_user.role == "admin" else "👤 Пользователь"
    await message.answer(
        f"ℹ️ <b>Справка</b>\n\n"
        f"Ваша роль: {role_label}\n\n"
        f"<b>Команды:</b>\n"
        f"/start — приветствие и открытие приложения\n"
        f"/plan — текущий тарифный план\n"
        f"/subscribe — улучшить тариф\n"
        f"/invite — код приглашения (для владельцев)\n"
        f"/help — эта справка",
        reply_markup=_webapp_keyboard(),
    )


# ── Онбординг: создать воркспейс ──────────────────────────────────────────────

@router.callback_query(F.data == "ws_create")
async def ws_create_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkspaceStates.entering_name)
    await call.message.edit_text(
        "🏢 <b>Создание рабочего пространства</b>\n\n"
        "Введите название вашей компании или ИП:\n"
        "<i>(например: ИП Иванов, ООО Ромашка)</i>",
    )


@router.message(WorkspaceStates.entering_name)
async def ws_create_finish(message: Message, state: FSMContext, db_user: User, session: AsyncSession) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer("Название должно быть от 2 до 100 символов. Попробуйте снова:")
        return

    async with session.begin():
        ws = await crud.create_workspace(session, name=name, owner_id=db_user.id)
        await crud.set_user_workspace(session, db_user.id, ws.id, role="admin")

    await state.clear()
    await message.answer(
        f"✅ <b>Рабочее пространство создано!</b>\n\n"
        f"🏢 <b>{ws.name}</b>\n"
        f"🔑 Код приглашения: <code>{ws.invite_code}</code>\n\n"
        f"<i>Поделитесь кодом с коллегами, чтобы они могли присоединиться.</i>\n\n"
        f"📋 Тариф: <b>Free</b> (1 ИП, 2 участника)\n"
        f"Для расширения используйте /subscribe",
        reply_markup=_webapp_keyboard(),
    )


# ── Онбординг: присоединиться по коду ────────────────────────────────────────

@router.callback_query(F.data == "ws_join")
async def ws_join_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkspaceStates.entering_invite_code)
    await call.message.edit_text(
        "🔑 <b>Присоединиться к пространству</b>\n\n"
        "Введите код приглашения (8 символов):",
    )


@router.message(WorkspaceStates.entering_invite_code)
async def ws_join_finish(message: Message, state: FSMContext, db_user: User, session: AsyncSession) -> None:
    code = message.text.strip().upper()
    async with session.begin():
        ws = await crud.get_workspace_by_invite(session, code)
        if ws is None:
            await message.answer("❌ Неверный код. Попробуйте ещё раз:")
            return

        # Проверяем лимит участников
        member_count = await crud.get_workspace_member_count(session, ws.id)
        limit = PLAN_LIMITS.get(ws.plan, PLAN_LIMITS["free"])["members"]
        if member_count >= limit:
            plan_label = PLAN_LIMITS.get(ws.plan, {}).get("label", ws.plan)
            await message.answer(
                f"❌ Рабочее пространство достигло лимита участников для тарифа {plan_label} ({limit}).\n"
                f"Попросите владельца обновить подписку."
            )
            return

        await crud.set_user_workspace(session, db_user.id, ws.id, role="user")

    await state.clear()
    await message.answer(
        f"✅ <b>Вы присоединились!</b>\n\n"
        f"🏢 <b>{ws.name}</b>\n\n"
        f"Используйте кнопку ниже для работы с бухгалтерией.",
        reply_markup=_webapp_keyboard(),
    )


# ── /plan — текущий тариф ─────────────────────────────────────────────────────

@router.message(Command("plan"))
async def cmd_plan(message: Message, db_user: User, session: AsyncSession) -> None:
    if not db_user.workspace_id:
        await message.answer(
            "У вас нет рабочего пространства. Используйте /start для создания.",
        )
        return

    ws = await crud.get_workspace(session, db_user.workspace_id)
    if ws is None:
        await message.answer("Рабочее пространство не найдено.")
        return

    plan = ws.plan
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    ip_count = await crud.count_ips(session, ws.id)
    member_count = await crud.get_workspace_member_count(session, ws.id)

    sub_info = ""
    if plan != "free" and ws.sub_end:
        end = ws.sub_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        days_left = (end - datetime.now(timezone.utc)).days
        if days_left > 0:
            sub_info = f"\n📅 Подписка до: <b>{end.strftime('%d.%m.%Y')}</b> ({days_left} дн.)"
        else:
            sub_info = "\n⚠️ Подписка <b>истекла</b>"

    await message.answer(
        f"📋 <b>Тарифный план</b>\n\n"
        f"Пространство: <b>{ws.name}</b>\n"
        f"Тариф: <b>{limits['label']}</b>{sub_info}\n\n"
        f"ИП: <b>{ip_count}</b> / {limits['ips']}\n"
        f"Участники: <b>{member_count}</b> / {limits['members']}\n\n"
        f"Тарифы:\n"
        f"• Free — 1 ИП, 2 участника\n"
        f"• Pro ⭐ — 5 ИП, 10 участников ({settings.pro_price_stars} ⭐/мес)\n"
        f"• Business 💎 — без ограничений ({settings.business_price_stars} ⭐/мес)\n\n"
        f"/subscribe — улучшить тариф",
    )


# ── /subscribe — подписка ─────────────────────────────────────────────────────

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, db_user: User, session: AsyncSession) -> None:
    if not db_user.workspace_id:
        await message.answer("Сначала создайте рабочее пространство через /start")
        return

    ws = await crud.get_workspace(session, db_user.workspace_id)
    if ws is None or ws.owner_id != db_user.id:
        await message.answer("Управлять подпиской может только владелец пространства.")
        return

    await message.answer(
        f"💳 <b>Выберите тариф</b>\n\n"
        f"⭐ <b>Pro</b> — {settings.pro_price_stars} Stars/мес\n"
        f"  • До 5 ИП\n"
        f"  • До 10 участников\n\n"
        f"💎 <b>Business</b> — {settings.business_price_stars} Stars/мес\n"
        f"  • Без ограничений на ИП\n"
        f"  • Без ограничений на участников\n",
        reply_markup=_subscribe_keyboard(),
    )


@router.callback_query(F.data.in_({"sub_pro", "sub_business"}))
async def sub_pay(call: CallbackQuery, db_user: User, bot: Bot) -> None:
    plan = "pro" if call.data == "sub_pro" else "business"
    stars = settings.pro_price_stars if plan == "pro" else settings.business_price_stars
    label = PLAN_LIMITS[plan]["label"]

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Подписка {label}",
        description=f"Бухгалтер ИП — тариф {label} на 30 дней",
        payload=f"sub_{plan}_{db_user.workspace_id}",
        currency="XTR",
        prices=[LabeledPrice(label=f"Подписка {label}", amount=stars)],
    )
    await call.answer()


@router.callback_query(F.data == "sub_cancel")
async def sub_cancel(call: CallbackQuery) -> None:
    await call.message.edit_text("Отменено.", reply_markup=None)


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, db_user: User, session: AsyncSession) -> None:
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    if len(parts) < 3 or parts[0] != "sub":
        return

    plan = parts[1]
    workspace_id = int(parts[2])

    async with session.begin():
        ws = await crud.get_workspace(session, workspace_id)
        if ws and ws.owner_id == db_user.id:
            now = datetime.now(timezone.utc)
            if ws.sub_end and ws.sub_end > now:
                new_end = ws.sub_end + timedelta(days=30)
            else:
                new_end = now + timedelta(days=30)
            await crud.set_workspace_plan(session, workspace_id, plan, new_end)

    plan_label = PLAN_LIMITS.get(plan, {}).get("label", plan)
    await message.answer(
        f"✅ <b>Оплата прошла!</b>\n\n"
        f"Тариф: <b>{plan_label}</b>\n"
        f"Действует 30 дней.",
        reply_markup=_webapp_keyboard(),
    )


# ── /invite — код приглашения ─────────────────────────────────────────────────

@router.message(Command("invite"))
async def cmd_invite(message: Message, db_user: User, session: AsyncSession) -> None:
    if not db_user.workspace_id:
        await message.answer("У вас нет рабочего пространства.")
        return

    ws = await crud.get_workspace(session, db_user.workspace_id)
    if ws is None:
        await message.answer("Рабочее пространство не найдено.")
        return

    if ws.owner_id != db_user.id:
        await message.answer("Код приглашения доступен только владельцу пространства.")
        return

    member_count = await crud.get_workspace_member_count(session, ws.id)
    limits = PLAN_LIMITS.get(ws.plan, PLAN_LIMITS["free"])

    await message.answer(
        f"🔑 <b>Код приглашения</b>\n\n"
        f"Пространство: <b>{ws.name}</b>\n"
        f"Код: <code>{ws.invite_code}</code>\n\n"
        f"Участники: {member_count} / {limits['members']}\n\n"
        f"Отправьте этот код коллеге. Он введёт его в боте через /start.",
    )


# ── Неизвестные сообщения ─────────────────────────────────────────────────────

@router.message(F.text)
async def unknown_message(message: Message, db_user: User) -> None:
    if not db_user.workspace_id:
        await message.answer(
            "Используй кнопки выше для настройки рабочего пространства.",
            reply_markup=_onboarding_keyboard(),
        )
        return
    await message.answer(
        "Используй кнопку ниже для открытия приложения 👇",
        reply_markup=_webapp_keyboard(),
    )
