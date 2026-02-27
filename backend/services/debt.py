"""
Сервис управления долгами.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import Debt, User


async def get_user_debts(
    session: AsyncSession, user_id: int
) -> tuple[list[Debt], list[Debt]]:
    """
    Возвращает долги пользователя:
    - owed_to_me: список долгов, где пользователь — кредитор (ему должны)
    - i_owe:      список долгов, где пользователь — должник (он должен)
    """
    return await crud.get_active_debts_for_user(session, user_id)


async def format_debts_text(
    owed_to_me: list[Debt], i_owe: list[Debt]
) -> str:
    """Формирует читаемый текст со списком долгов."""
    lines = ["🔴 <b>Долги</b>\n"]

    if owed_to_me:
        lines.append("<b>Вам должны:</b>")
        for d in owed_to_me:
            name = d.debtor.display_name
            lines.append(f"  • {name}: {d.amount:,} ₽".replace(",", "\u202f"))
    else:
        lines.append("<b>Вам должны:</b> нет")

    lines.append("")

    if i_owe:
        lines.append("<b>Вы должны:</b>")
        for d in i_owe:
            name = d.creditor.display_name
            lines.append(f"  • {name}: {d.amount:,} ₽".replace(",", "\u202f"))
    else:
        lines.append("<b>Вы должны:</b> нет")

    return "\n".join(lines)
