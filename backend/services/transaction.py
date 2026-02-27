"""
Сервис проведения финансовых операций.
Все операции выполняются в рамках транзакции, открытой в get_session.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import Transaction, TxType

logger = logging.getLogger(__name__)


class InsufficientFundsError(ValueError):
    """Недостаточно средств для операции."""
    pass


async def process_operation(
    session: AsyncSession,
    user_id: int,
    op_type: str,
    amount: int,
    ip_id: int | None = None,
    target_user_id: int | None = None,
    comment: str | None = None,
) -> Transaction:
    """
    Проводит финансовую операцию атомарно.
    Транзакция управляется на уровне get_session (одна на весь запрос).
    """
    user = await crud.get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")

    # ── Закуп ────────────────────────────────────────────────────────────
    if op_type == TxType.ZAKUP:
        if user.cash_balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно наличных.\nВаш баланс: {user.cash_balance:,} ₽"
            )
        await crud.update_cash_balance(session, user_id, -amount)
        await crud.update_ip_cash(session, ip_id, +amount)

    # ── Посторонние траты ─────────────────────────────────────────────────
    elif op_type == TxType.STORONNIE:
        if user.cash_balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно наличных.\nВаш баланс: {user.cash_balance:,} ₽"
            )
        await crud.update_cash_balance(session, user_id, -amount)

    # ── Приходы ───────────────────────────────────────────────────────────
    elif op_type in (TxType.PRIHOD_MES, TxType.PRIHOD_FAST, TxType.PRIHOD_STO):
        await crud.update_cash_balance(session, user_id, +amount)

    # ── Снять с Р/С → личный баланс ──────────────────────────────────────
    elif op_type == TxType.SNYAT_RS:
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.bank_balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно средств на Р/С.\nОстаток: {ip.bank_balance:,} ₽"
            )
        await crud.update_ip_bank(session, ip_id, -amount)
        await crud.update_cash_balance(session, user_id, +amount)

    # ── Внести на Р/С ← личный баланс ────────────────────────────────────
    elif op_type == TxType.VNESTI_RS:
        if user.cash_balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно наличных.\nВаш баланс: {user.cash_balance:,} ₽"
            )
        await crud.update_cash_balance(session, user_id, -amount)
        await crud.update_ip_bank(session, ip_id, +amount)

    # ── Одолжить ─────────────────────────────────────────────────────────
    elif op_type == TxType.ODOLZHIT:
        if user.cash_balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно наличных.\nВаш баланс: {user.cash_balance:,} ₽"
            )
        await crud.update_cash_balance(session, user_id, -amount)
        await crud.update_cash_balance(session, target_user_id, +amount)
        await crud.create_debt(session, user_id, target_user_id, amount)

    else:
        raise ValueError(f"Неизвестный тип операции: {op_type}")

    tx = await crud.create_transaction(
        session,
        user_id=user_id,
        tx_type=op_type,
        amount=amount,
        ip_id=ip_id,
        comment=comment,
    )

    logger.info(
        "Операция [%s] user=%d amount=%d ip=%s",
        op_type, user_id, amount, ip_id,
    )
    return tx


async def repay_debt_operation(
    session: AsyncSession,
    debt_id: int,
    payer_id: int,
    amount: int,
) -> Transaction:
    """
    Погашение долга: должник платит кредитору.
    payer_id — Telegram ID того, кто гасит долг (должник).
    """
    debt = await crud.get_debt_by_id(session, debt_id)
    if debt is None:
        raise ValueError("Долг не найден")
    if debt.debtor_id != payer_id:
        raise ValueError("Вы не являетесь должником по этому долгу")

    payer = await crud.get_user(session, payer_id)
    if payer.cash_balance < amount:
        raise InsufficientFundsError(
            f"Недостаточно наличных.\nВаш баланс: {payer.cash_balance:,} ₽"
        )

    await crud.update_cash_balance(session, payer_id, -amount)
    await crud.update_cash_balance(session, debt.creditor_id, +amount)
    await crud.repay_debt(session, debt_id, amount)

    tx = await crud.create_transaction(
        session,
        user_id=payer_id,
        tx_type=TxType.POGASIT,
        amount=amount,
        comment=f"Погашение долга #{debt_id}",
    )

    logger.info("Долг #%d погашен на %d ₽ пользователем %d", debt_id, amount, payer_id)
    return tx
