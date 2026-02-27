"""
Сервис сводок и отчётов.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import EXPENSE_TYPES, INCOME_TYPES, TxType


PERIOD_LABELS = {
    "today": "сегодня",
    "week":  "за неделю",
    "month": "за месяц",
    "all":   "за всё время",
}


def _period_start(period: str) -> datetime | None:
    """Возвращает дату начала периода (UTC) или None для 'всё время'."""
    now = datetime.now(tz=timezone.utc)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None  # all


async def get_personal_report(
    session: AsyncSession, user_id: int, period: str
) -> str:
    """
    Формирует текстовую сводку для конкретного пользователя.
    Включает: личные приходы/расходы, балансы ИП, долги.
    """
    since = _period_start(period)
    label = PERIOD_LABELS.get(period, period)

    # Транзакции пользователя за период
    txs = await crud.get_transactions(session, user_id=user_id, since=since)
    income = sum(t.amount for t in txs if t.type in INCOME_TYPES)
    expense = sum(t.amount for t in txs if t.type in EXPENSE_TYPES)

    # Текущий баланс
    user = await crud.get_user(session, user_id)
    user_cash = user.cash_balance if user else 0

    # Балансы ИП
    ips = await crud.get_all_ips(session)

    # Долги
    owed_to_me, i_owe = await crud.get_active_debts_for_user(session, user_id)
    total_owed_to_me = sum(d.amount for d in owed_to_me)
    total_i_owe = sum(d.amount for d in i_owe)

    def fmt(n: int) -> str:
        return f"{n:,}".replace(",", "\u202f") + " ₽"

    lines = [
        f"📊 <b>Сводка {label}</b>\n",
        f"📥 Приход:  <b>+{fmt(income)}</b>",
        f"📤 Расход:  <b>-{fmt(expense)}</b>",
        f"💳 Ваш баланс (нал): <b>{fmt(user_cash)}</b>",
        "",
        "🏦 <b>Балансы ИП:</b>",
    ]

    if ips:
        for ip in ips:
            lines.append(
                f"  • {ip.name}: Р/С {fmt(ip.bank_balance)} | Нал {fmt(ip.cash_balance)}"
            )
    else:
        lines.append("  нет ИП")

    lines += [
        "",
        "💰 <b>Долги:</b>",
        f"  Вам должны: {fmt(total_owed_to_me)}",
        f"  Вы должны:  {fmt(total_i_owe)}",
    ]

    return "\n".join(lines)
