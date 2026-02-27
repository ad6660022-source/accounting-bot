"""
Сервис сводок и отчётов.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import EXPENSE_TYPES, INCOME_TYPES


PERIOD_LABELS = {
    "today": "сегодня",
    "week":  "за неделю",
    "month": "за месяц",
    "all":   "за всё время",
}


def _period_start(period: str) -> datetime | None:
    now = datetime.now(tz=timezone.utc)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None


async def get_personal_report(
    session: AsyncSession, user_id: int, period: str
) -> str:
    since = _period_start(period)
    label = PERIOD_LABELS.get(period, period)

    txs = await crud.get_transactions(session, user_id=user_id, since=since)
    income = sum(t.amount for t in txs if t.type in INCOME_TYPES)
    expense = sum(t.amount for t in txs if t.type in EXPENSE_TYPES)

    ips = await crud.get_all_ips(session)
    ip_debts = await crud.get_active_ip_debts(session)

    def fmt(n: int) -> str:
        return f"{n:,}".replace(",", "\u202f") + " \u20bd"

    header = "📊 <b>Сводка " + label + "</b>"
    lines = [
        header,
        "",
        "📥 Приход:  <b>+" + fmt(income) + "</b>",
        "📤 Расход:  <b>-" + fmt(expense) + "</b>",
        "",
        "🏦 <b>Балансы ИП:</b>",
    ]

    if ips:
        for ip in ips:
            lines.append(
                "  \u2022 " + ip.name + ": Р/С " + fmt(ip.bank_balance)
                + " | Деб " + fmt(ip.debit_balance)
                + " | Нал " + fmt(ip.cash_balance)
            )
    else:
        lines.append("  нет ИП")

    if ip_debts:
        lines += ["", "🔴 <b>Долги между ИП:</b>"]
        for d in ip_debts:
            lines.append("  \u2022 " + d.debtor_ip.name + " \u2192 " + d.creditor_ip.name + ": " + fmt(d.amount))
    else:
        lines += ["", "✅ Долгов между ИП нет"]

    return "\n".join(lines)
