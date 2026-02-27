import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import crud
from backend.database.models import Transaction, TxType

logger = logging.getLogger(__name__)


class InsufficientFundsError(ValueError):
    pass


async def process_operation(session, user_id, op_type, amount, ip_id=None, target_ip_id=None, comment=None):
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

    tx = await crud.create_transaction(session, user_id=user_id, tx_type=op_type, amount=amount, ip_id=ip_id, comment=comment)
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
