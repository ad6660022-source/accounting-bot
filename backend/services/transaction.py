import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import crud
from backend.database.models import Transaction, TxType

logger = logging.getLogger(__name__)


class InsufficientFundsError(ValueError):
    pass


async def process_operation(session, user_id, op_type, amount, ip_id=None, target_ip_id=None, comment=None, destination=None):
    user = await crud.get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")

    if op_type == TxType.ZAKUP:
        if ip_id is None:
            raise ValueError("Не указано ИП")
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.cash_balance < amount:
            raise InsufficientFundsError(f"Недостаточно наличных у ИП.\nОстаток: {ip.cash_balance:,} ₽")
        await crud.update_ip_cash(session, ip_id, -amount)

    elif op_type == TxType.STORONNIE:
        if ip_id is None:
            raise ValueError("Не указано ИП")
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.cash_balance < amount:
            raise InsufficientFundsError(f"Недостаточно наличных у ИП.\nОстаток: {ip.cash_balance:,} ₽")
        await crud.update_ip_cash(session, ip_id, -amount)

    elif op_type in (TxType.PRIHOD_MES, TxType.PRIHOD_FAST, TxType.PRIHOD_STO):
        if ip_id is None:
            raise ValueError("Не указано ИП")
        dest = destination or "cash"
        if dest == "bank":
            await crud.update_ip_bank(session, ip_id, +amount)
        elif dest == "debit":
            await crud.update_ip_debit(session, ip_id, +amount)
        else:
            await crud.update_ip_cash(session, ip_id, +amount)

    elif op_type == TxType.SNYAT_RS:
        if ip_id is None:
            raise ValueError("Не указано ИП")
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.bank_balance < amount:
            raise InsufficientFundsError(f"Недостаточно средств на Р/С.\nОстаток: {ip.bank_balance:,} ₽")
        await crud.update_ip_bank(session, ip_id, -amount)
        await crud.update_ip_debit(session, ip_id, +amount)

    elif op_type == TxType.SNYAT_DEBIT:
        if ip_id is None:
            raise ValueError("Не указано ИП")
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.debit_balance < amount:
            raise InsufficientFundsError(f"Недостаточно средств на Дебете.\nОстаток: {ip.debit_balance:,} ₽")
        await crud.update_ip_debit(session, ip_id, -amount)
        await crud.update_ip_cash(session, ip_id, +amount)

    elif op_type == TxType.VNESTI_RS:
        if ip_id is None:
            raise ValueError("Не указано ИП")
        ip = await crud.get_ip(session, ip_id)
        if ip is None:
            raise ValueError("ИП не найдено")
        if ip.cash_balance < amount:
            raise InsufficientFundsError(f"Недостаточно наличных у ИП.\nОстаток: {ip.cash_balance:,} ₽")
        await crud.update_ip_cash(session, ip_id, -amount)
        await crud.update_ip_bank(session, ip_id, +amount)

    elif op_type == TxType.ODOLZHIT:
        if ip_id is None:
            raise ValueError("Не указано ИП-кредитор")
        if target_ip_id is None:
            raise ValueError("Не указано ИП-заёмщик")
        creditor_ip = await crud.get_ip(session, ip_id)
        if creditor_ip is None:
            raise ValueError("ИП-кредитор не найдено")
        if creditor_ip.cash_balance < amount:
            raise InsufficientFundsError(f"Недостаточно наличных у ИП.\nОстаток: {creditor_ip.cash_balance:,} ₽")
        await crud.update_ip_cash(session, ip_id, -amount)
        await crud.update_ip_cash(session, target_ip_id, +amount)
        await crud.create_ip_debt(session, ip_id, target_ip_id, amount)

    else:
        raise ValueError(f"Неизвестный тип операции: {op_type}")

    tx = await crud.create_transaction(session, user_id=user_id, tx_type=op_type, amount=amount, ip_id=ip_id, comment=comment, destination=destination)
    logger.info("Операция [%s] user=%d amount=%d ip=%s", op_type, user_id, amount, ip_id)
    return tx


async def repay_ip_debt_operation(session, debt_id, amount, user_id):
    debt = await crud.get_ip_debt_by_id(session, debt_id)
    if debt is None:
        raise ValueError("Долг не найден")
    if debt.is_paid:
        raise ValueError("Долг уже погашен")
    if amount > debt.amount:
        raise ValueError(f"Сумма превышает остаток долга: {debt.amount:,} ₽")
    debtor_ip = await crud.get_ip(session, debt.debtor_ip_id)
    if debtor_ip.cash_balance < amount:
        raise InsufficientFundsError(f"Недостаточно наличных у ИП-заёмщика.\nОстаток: {debtor_ip.cash_balance:,} ₽")
    await crud.update_ip_cash(session, debt.debtor_ip_id, -amount)
    await crud.update_ip_cash(session, debt.creditor_ip_id, +amount)
    await crud.repay_ip_debt(session, debt_id, amount)
    tx = await crud.create_transaction(session, user_id=user_id, tx_type=TxType.POGASIT, amount=amount, ip_id=debt.creditor_ip_id, comment=f"Погашение долга #{debt_id}")
    logger.info("Долг ИП #%d погашен на %d ₽", debt_id, amount)
    return tx


def _get_balance_delta(tx: Transaction) -> tuple[int, int, int]:
    """Возвращает (delta_cash, delta_bank, delta_debit) для транзакции."""
    t = tx.type
    a = tx.amount
    dest = tx.destination or "cash"

    if t in (TxType.ZAKUP, TxType.STORONNIE, TxType.EXPENSE_WRITEOFF):
        src = dest if t == TxType.EXPENSE_WRITEOFF else "cash"
        if src == "bank":
            return (0, -a, 0)
        elif src == "debit":
            return (0, 0, -a)
        return (-a, 0, 0)
    elif t in (TxType.PRIHOD_MES, TxType.PRIHOD_FAST, TxType.PRIHOD_STO):
        if dest == "bank":
            return (0, a, 0)
        elif dest == "debit":
            return (0, 0, a)
        return (a, 0, 0)
    elif t == TxType.SNYAT_RS:
        return (0, -a, a)
    elif t == TxType.SNYAT_DEBIT:
        return (a, 0, -a)
    elif t == TxType.VNESTI_RS:
        return (-a, a, 0)
    elif t in (TxType.ODOLZHIT, TxType.POGASIT):
        return (-a, 0, 0)
    return (0, 0, 0)


async def cancel_operation(session, tx_id: int, admin_id: int) -> Transaction:
    tx = await crud.get_transaction(session, tx_id)
    if tx is None:
        raise ValueError("Операция не найдена")
    if tx.is_cancelled:
        raise ValueError("Операция уже отменена")

    if tx.ip_id is not None:
        dc, db, dd = _get_balance_delta(tx)
        # Reversal: apply negative of the original delta
        if dc != 0:
            await crud.update_ip_cash(session, tx.ip_id, -dc)
        if db != 0:
            await crud.update_ip_bank(session, tx.ip_id, -db)
        if dd != 0:
            await crud.update_ip_debit(session, tx.ip_id, -dd)

        # For ODOLZHIT: also reverse the target IP's balance
        if tx.type == TxType.ODOLZHIT:
            # The target_ip received +amount cash; find associated debt for the target ip
            from sqlalchemy import select
            from backend.database.models import IpDebt
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(IpDebt).where(
                    IpDebt.creditor_ip_id == tx.ip_id,
                    IpDebt.is_paid.is_(False),
                ).order_by(IpDebt.created_at.desc()).limit(1)
            )
            debt = result.scalar_one_or_none()
            if debt is not None:
                await crud.update_ip_cash(session, debt.debtor_ip_id, -tx.amount)
                debt.is_paid = True

    tx.is_cancelled = True
    tx.cancelled_at = datetime.utcnow()
    tx.cancelled_by_id = admin_id
    logger.info("Операция #%d отменена администратором %d", tx_id, admin_id)
    return tx


async def edit_operation(session, tx_id: int, admin_id: int, new_amount: int | None = None, new_comment: str | None = None) -> Transaction:
    tx = await crud.get_transaction(session, tx_id)
    if tx is None:
        raise ValueError("Операция не найдена")
    if tx.is_cancelled:
        raise ValueError("Нельзя редактировать отменённую операцию")

    if new_amount is not None and new_amount != tx.amount:
        if new_amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        if tx.ip_id is not None:
            old_dc, old_db, old_dd = _get_balance_delta(tx)
            # temporarily update tx.amount for delta calculation
            old_amount = tx.amount
            tx.amount = new_amount
            new_dc, new_db, new_dd = _get_balance_delta(tx)
            tx.amount = old_amount

            diff_dc = new_dc - old_dc
            diff_db = new_db - old_db
            diff_dd = new_dd - old_dd
            if diff_dc != 0:
                await crud.update_ip_cash(session, tx.ip_id, diff_dc)
            if diff_db != 0:
                await crud.update_ip_bank(session, tx.ip_id, diff_db)
            if diff_dd != 0:
                await crud.update_ip_debit(session, tx.ip_id, diff_dd)

        tx.amount = new_amount

    if new_comment is not None:
        tx.comment = new_comment.strip() or None

    logger.info("Операция #%d отредактирована администратором %d", tx_id, admin_id)
    return tx


async def write_off_expense(session, expense_id: int, ip_id: int, amount: int, source: str, user_id: int) -> Transaction:
    expense = await crud.get_expense(session, expense_id)
    if expense is None:
        raise ValueError("Расход не найден")
    ip = await crud.get_ip(session, ip_id)
    if ip is None:
        raise ValueError("ИП не найдено")
    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля")

    if source == "bank":
        if ip.bank_balance < amount:
            raise InsufficientFundsError(f"Недостаточно средств на Р/С. Остаток: {ip.bank_balance:,} ₽")
        await crud.update_ip_bank(session, ip_id, -amount)
    elif source == "debit":
        if ip.debit_balance < amount:
            raise InsufficientFundsError(f"Недостаточно средств на Дебете. Остаток: {ip.debit_balance:,} ₽")
        await crud.update_ip_debit(session, ip_id, -amount)
    else:  # cash
        if ip.cash_balance < amount:
            raise InsufficientFundsError(f"Недостаточно наличных у ИП. Остаток: {ip.cash_balance:,} ₽")
        await crud.update_ip_cash(session, ip_id, -amount)

    tx = Transaction(
        user_id=user_id,
        ip_id=ip_id,
        type=TxType.EXPENSE_WRITEOFF,
        amount=amount,
        comment=expense.description,
        destination=source,
        expense_id=expense_id,
    )
    session.add(tx)
    await session.flush()
    logger.info("Расход #%d списан с ИП #%d на %d ₽ (%s)", expense_id, ip_id, amount, source)
    return tx
