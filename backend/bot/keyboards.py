"""
Inline-клавиатуры для всех экранов бота.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.database.models import Debt, IP, TxType, User


# ── Главное меню ──────────────────────────────────────────────────────────────

def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Баланс",    callback_data="menu_balance"),
        InlineKeyboardButton(text="➕ Операция",  callback_data="menu_operation"),
    )
    builder.row(
        InlineKeyboardButton(text="🔴 Долги",    callback_data="menu_debts"),
        InlineKeyboardButton(text="📊 Сводка",   callback_data="menu_report"),
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Управление", callback_data="menu_admin"),
        )
    return builder.as_markup()


# ── Операции ──────────────────────────────────────────────────────────────────

OPERATION_BUTTONS = [
    ("🛒 Закуп",              TxType.ZAKUP),
    ("💸 Посторонние траты",  TxType.STORONNIE),
    ("📥 Приход ежемес.",     TxType.PRIHOD_MES),
    ("⚡ Приход быстрый",     TxType.PRIHOD_FAST),
    ("🏦 Приход сторонний",   TxType.PRIHOD_STO),
    ("💴 Снять с Р/С",        TxType.SNYAT_RS),
    ("🏛 Внести на Р/С",      TxType.VNESTI_RS),
    ("🤝 Одолжить",           TxType.ODOLZHIT),
]


def operations_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, op_type in OPERATION_BUTTONS:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"op_{op_type}"))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Список ИП ─────────────────────────────────────────────────────────────────

def ip_list_kb(ips: list[IP]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ip in ips:
        builder.row(
            InlineKeyboardButton(text=ip.name, callback_data=f"ip_{ip.id}")
        )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Список пользователей (кому одолжить) ──────────────────────────────────────

def users_list_kb(users: list[User], exclude_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for u in users:
        if u.id == exclude_id:
            continue
        label = u.display_name
        builder.row(InlineKeyboardButton(text=label, callback_data=f"tgt_{u.id}"))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Подтверждение операции ────────────────────────────────────────────────────

def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Отмена",       callback_data="back_main"),
    )
    return builder.as_markup()


# ── Выбор периода для сводки ──────────────────────────────────────────────────

def period_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Сегодня",    callback_data="period_today"),
        InlineKeyboardButton(text="Неделя",     callback_data="period_week"),
    )
    builder.row(
        InlineKeyboardButton(text="Месяц",      callback_data="period_month"),
        InlineKeyboardButton(text="Всё время",  callback_data="period_all"),
    )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Меню администратора ───────────────────────────────────────────────────────

def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Создать ИП",    callback_data="admin_create_ip"),
    )
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи",  callback_data="admin_users"),
    )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Долги с кнопкой погашения ─────────────────────────────────────────────────

def debts_kb(i_owe: list[Debt]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in i_owe:
        name = d.creditor.display_name
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Погасить долг → {name}",
                callback_data=f"repay_{d.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Управление пользователями ─────────────────────────────────────────────────

def user_manage_kb(users: list[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for u in users:
        role_icon = "👑" if u.role == "admin" else "👤"
        builder.row(
            InlineKeyboardButton(
                text=f"{role_icon} {u.display_name} ({u.cash_balance:,} ₽)".replace(",", "\u202f"),
                callback_data=f"manage_{u.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="menu_admin"))
    return builder.as_markup()


def user_role_kb(user_id: int, current_role: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_role != "admin":
        builder.row(
            InlineKeyboardButton(
                text="👑 Сделать администратором",
                callback_data=f"setrole_{user_id}_admin",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="👤 Снять права администратора",
                callback_data=f"setrole_{user_id}_user",
            )
        )
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="admin_users"))
    return builder.as_markup()


# ── Кнопка «Назад» ───────────────────────────────────────────────────────────

def back_to_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="back_main"))
    return builder.as_markup()
