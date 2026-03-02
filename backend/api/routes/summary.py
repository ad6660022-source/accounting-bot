"""
Эндпоинт отправки мини-сводки в Telegram.
Отправляет текущее состояние балансов ИП и долгов пользователю в личку.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import User

router = APIRouter()


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", "\u202f") + "\u00a0\u20bd"


def _build_summary_text(ips, debts) -> str:
    lines = ["📊 <b>Сводка балансов</b>", ""]
    if ips:
        for ip in ips:
            lines.append(f"🏢 <b>{ip.name}</b>")
            lines.append(f"  Р/С:    {_fmt(ip.bank_balance)}")
            lines.append(f"  Дебет:  {_fmt(ip.debit_balance)}")
            lines.append(f"  Нал:    {_fmt(ip.cash_balance)}")
            lines.append("")
    else:
        lines += ["Нет ИП", ""]

    if debts:
        lines.append("🔴 <b>Долги между ИП:</b>")
        for d in debts:
            lines.append(f"  • {d.debtor_ip.name} → {d.creditor_ip.name}: {_fmt(d.amount)}")
    else:
        lines.append("✅ Долгов между ИП нет")

    return "\n".join(lines)


@router.post("/summary/send")
async def send_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ips = await crud.get_all_ips(session)
    debts = await crud.get_active_ip_debts(session)
    text = _build_summary_text(ips, debts)

    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        return {"ok": False, "error": "Бот недоступен"}

    await bot.send_message(current_user.id, text, parse_mode="HTML")
    return {"ok": True}
