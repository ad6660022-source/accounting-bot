from __future__ import annotations
import logging
from datetime import datetime
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database.models import IpDebt, Transaction, User, IP

logger = logging.getLogger(__name__)

async def get_user(session, user_id):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_all_users(session):
    result = await session.execute(select(User).order_by(User.username))
    return list(result.scalars().all())

async def get_or_create_user(session, user_id, username, admin_ids=None):
    user = await get_user(session, user_id)
    if user is None:
        role = "admin" if (admin_ids and user_id in admin_ids) else "user"
        user = User(id=user_id, username=username, role=role)
        session.add(user)
        await session.flush()
        logger.info("Новый пользователь: %s (роль: %s)", user.display_name, role)
    else:
        if user.username != username:
            user.username = username
    return user

async def update_cash_balance(session, user_id, delta):
    user = await get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")
    user.cash_balance += delta
    return user

async def set_user_role(session, user_id, role):
    user = await get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")
    user.role = role
    return user

async def create_ip(session, name, bank_balance=0, cash_balance=0):
    ip = IP(name=name, bank_balance=bank_balance, debit_balance=0, cash_balance=cash_balance, initial_capital=bank_balance + cash_balance)
    session.add(ip)
    await session.flush()
    return ip

async def set_ip_balances(session, ip_id, bank_balance, cash_balance):
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.bank_balance = bank_balance
    ip.cash_balance = cash_balance
    return ip

async def get_ip(session, ip_id):
    result = await session.execute(select(IP).where(IP.id == ip_id))
    return result.scalar_one_or_none()

async def get_ip_by_name(session, name):
    result = await session.execute(select(IP).where(IP.name == name))
    return result.scalar_one_or_none()

async def get_all_ips(session):
    result = await session.execute(select(IP).order_by(IP.name))
    return list(result.scalars().all())

async def update_ip_bank(session, ip_id, delta):
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.bank_balance += delta
    return ip

async def update_ip_debit(session, ip_id, delta):
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.debit_balance += delta
    return ip

async def update_ip_cash(session, ip_id, delta):
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.cash_balance += delta
    return ip

async def create_transaction(session, user_id, tx_type, amount, ip_id=None, comment=None):
    tx = Transaction(user_id=user_id, ip_id=ip_id, type=tx_type, amount=amount, comment=comment)
    session.add(tx)
    await session.flush()
    return tx

async def get_transactions(session, *, user_id=None, ip_id=None, since=None, limit=100):
    query = (
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.ip))
        .order_by(Transaction.created_at.desc())
    )
    conditions = []
    if user_id is not None:
        conditions.append(Transaction.user_id == user_id)
    if ip_id is not None:
        conditions.append(Transaction.ip_id == ip_id)
    if since is not None:
        conditions.append(Transaction.created_at >= since)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())

async def create_ip_debt(session, creditor_ip_id, debtor_ip_id, amount):
    debt = IpDebt(creditor_ip_id=creditor_ip_id, debtor_ip_id=debtor_ip_id, amount=amount)
    session.add(debt)
    await session.flush()
    return debt

async def get_active_ip_debts(session):
    result = await session.execute(
        select(IpDebt)
        .options(selectinload(IpDebt.creditor_ip), selectinload(IpDebt.debtor_ip))
        .where(IpDebt.is_paid.is_(False))
        .order_by(IpDebt.created_at.desc())
    )
    return list(result.scalars().all())

async def get_ip_debt_by_id(session, debt_id):
    result = await session.execute(
        select(IpDebt)
        .options(selectinload(IpDebt.creditor_ip), selectinload(IpDebt.debtor_ip))
        .where(IpDebt.id == debt_id)
    )
    return result.scalar_one_or_none()

async def repay_ip_debt(session, debt_id, amount):
    debt = await get_ip_debt_by_id(session, debt_id)
    if debt is None:
        raise ValueError(f"Долг {debt_id} не найден")
    if debt.is_paid:
        raise ValueError("Долг уже погашен")
    debt.amount = max(0, debt.amount - amount)
    if debt.amount == 0:
        debt.is_paid = True
    return debt


async def reset_all_data(session: AsyncSession) -> None:
    """Удаляет все ИП, транзакции, долги. Пользователи остаются."""
    await session.execute(delete(IpDebt))
    await session.execute(delete(Transaction))
    await session.execute(delete(IP))
    # Обнуляем cash_balance у пользователей
    users = await get_all_users(session)
    for u in users:
        u.cash_balance = 0
    logger.info("Все данные сброшены")
