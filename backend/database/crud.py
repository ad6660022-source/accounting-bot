"""
CRUD-операции с базой данных.
Все функции принимают AsyncSession и НЕ управляют транзакциями самостоятельно —
управление транзакциями лежит на сервисном слое.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Debt, IP, Transaction, User

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ПОЛЬЗОВАТЕЛИ
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Получить пользователя по Telegram ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> list[User]:
    """Получить всех зарегистрированных пользователей."""
    result = await session.execute(select(User).order_by(User.username))
    return list(result.scalars().all())


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: str | None,
    admin_ids: list[int] | None = None,
) -> User:
    """
    Возвращает существующего пользователя или создаёт нового.
    Если user_id есть в admin_ids — назначает роль admin.
    """
    user = await get_user(session, user_id)
    if user is None:
        role = "admin" if (admin_ids and user_id in admin_ids) else "user"
        user = User(id=user_id, username=username, role=role)
        session.add(user)
        await session.flush()
        logger.info("Новый пользователь: %s (роль: %s)", user.display_name, role)
    else:
        # Обновляем username если изменился
        if user.username != username:
            user.username = username
    return user


async def update_cash_balance(
    session: AsyncSession, user_id: int, delta: int
) -> User:
    """Изменяет личный баланс пользователя на delta (может быть отрицательным)."""
    user = await get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")
    user.cash_balance += delta
    return user


async def set_user_role(session: AsyncSession, user_id: int, role: str) -> User:
    """Устанавливает роль пользователя (admin / user)."""
    user = await get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")
    user.role = role
    return user


# ═══════════════════════════════════════════════════════════════════════════════
# ИНДИВИДУАЛЬНЫЕ ПРЕДПРИНИМАТЕЛИ
# ═══════════════════════════════════════════════════════════════════════════════

async def create_ip(
    session: AsyncSession, name: str, bank_balance: int = 0, cash_balance: int = 0
) -> IP:
    """Создаёт новое ИП с указанными остатками на Р/С и в наличке."""
    ip = IP(
        name=name,
        bank_balance=bank_balance,
        cash_balance=cash_balance,
        initial_capital=bank_balance + cash_balance,
    )
    session.add(ip)
    await session.flush()
    logger.info("Создано ИП: %s (Р/С: %d ₽, нал: %d ₽)", name, bank_balance, cash_balance)
    return ip


async def set_ip_balances(
    session: AsyncSession, ip_id: int, bank_balance: int, cash_balance: int
) -> IP:
    """Устанавливает балансы ИП напрямую (корректировка для админа)."""
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.bank_balance = bank_balance
    ip.cash_balance = cash_balance
    return ip


async def get_ip(session: AsyncSession, ip_id: int) -> IP | None:
    """Получить ИП по ID."""
    result = await session.execute(select(IP).where(IP.id == ip_id))
    return result.scalar_one_or_none()


async def get_ip_by_name(session: AsyncSession, name: str) -> IP | None:
    """Получить ИП по названию."""
    result = await session.execute(select(IP).where(IP.name == name))
    return result.scalar_one_or_none()


async def get_all_ips(session: AsyncSession) -> list[IP]:
    """Получить все ИП, отсортированные по имени."""
    result = await session.execute(select(IP).order_by(IP.name))
    return list(result.scalars().all())


async def update_ip_bank(session: AsyncSession, ip_id: int, delta: int) -> IP:
    """Изменяет расчётный счёт ИП на delta."""
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.bank_balance += delta
    return ip


async def update_ip_cash(session: AsyncSession, ip_id: int, delta: int) -> IP:
    """Изменяет наличные ИП на delta."""
    ip = await get_ip(session, ip_id)
    if ip is None:
        raise ValueError(f"ИП {ip_id} не найдено")
    ip.cash_balance += delta
    return ip


# ═══════════════════════════════════════════════════════════════════════════════
# ТРАНЗАКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

async def create_transaction(
    session: AsyncSession,
    user_id: int,
    tx_type: str,
    amount: int,
    ip_id: int | None = None,
    comment: str | None = None,
) -> Transaction:
    """Записывает финансовую операцию в историю."""
    tx = Transaction(
        user_id=user_id,
        ip_id=ip_id,
        type=tx_type,
        amount=amount,
        comment=comment,
    )
    session.add(tx)
    await session.flush()
    return tx


async def get_transactions(
    session: AsyncSession,
    *,
    user_id: int | None = None,
    ip_id: int | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> list[Transaction]:
    """
    Получить историю операций с фильтрами.
    Загружает связанные объекты user и ip.
    """
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


# ═══════════════════════════════════════════════════════════════════════════════
# ДОЛГИ
# ═══════════════════════════════════════════════════════════════════════════════

async def create_debt(
    session: AsyncSession,
    creditor_id: int,
    debtor_id: int,
    amount: int,
) -> Debt:
    """Создаёт новый долг."""
    debt = Debt(creditor_id=creditor_id, debtor_id=debtor_id, amount=amount)
    session.add(debt)
    await session.flush()
    return debt


async def get_active_debts_for_user(
    session: AsyncSession, user_id: int
) -> tuple[list[Debt], list[Debt]]:
    """
    Возвращает (долги_где_кредитор=user, долги_где_должник=user).
    Загружает связанных пользователей.
    """
    # Долги, где пользователь — кредитор (ему должны)
    q_creditor = (
        select(Debt)
        .options(selectinload(Debt.debtor))
        .where(Debt.creditor_id == user_id, Debt.is_paid.is_(False))
    )
    # Долги, где пользователь — должник (он должен)
    q_debtor = (
        select(Debt)
        .options(selectinload(Debt.creditor))
        .where(Debt.debtor_id == user_id, Debt.is_paid.is_(False))
    )

    r1 = await session.execute(q_creditor)
    r2 = await session.execute(q_debtor)
    return list(r1.scalars().all()), list(r2.scalars().all())


async def get_debt_by_id(session: AsyncSession, debt_id: int) -> Debt | None:
    """Получить долг по ID."""
    result = await session.execute(
        select(Debt)
        .options(selectinload(Debt.creditor), selectinload(Debt.debtor))
        .where(Debt.id == debt_id)
    )
    return result.scalar_one_or_none()


async def repay_debt(
    session: AsyncSession, debt_id: int, amount: int
) -> Debt:
    """
    Погашает часть или весь долг.
    Если amount >= debt.amount — отмечает долг как погашенный.
    """
    debt = await get_debt_by_id(session, debt_id)
    if debt is None:
        raise ValueError(f"Долг {debt_id} не найден")
    if debt.is_paid:
        raise ValueError("Долг уже погашен")

    debt.amount = max(0, debt.amount - amount)
    if debt.amount == 0:
        debt.is_paid = True
    return debt
