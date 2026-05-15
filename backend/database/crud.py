from __future__ import annotations
import logging
import secrets
import string
from datetime import datetime
from sqlalchemy import select, and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database.models import Expense, IpDebt, Transaction, User, IP, Workspace

logger = logging.getLogger(__name__)


def _generate_invite_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


# ── Воркспейсы ────────────────────────────────────────────────────────────────

async def create_workspace(session: AsyncSession, name: str, owner_id: int) -> Workspace:
    code = _generate_invite_code()
    ws = Workspace(name=name, owner_id=owner_id, plan="free", invite_code=code)
    session.add(ws)
    await session.flush()
    return ws


async def get_workspace(session: AsyncSession, workspace_id: int) -> Workspace | None:
    result = await session.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def get_workspace_by_invite(session: AsyncSession, invite_code: str) -> Workspace | None:
    result = await session.execute(
        select(Workspace).where(Workspace.invite_code == invite_code.upper().strip())
    )
    return result.scalar_one_or_none()


async def set_workspace_plan(session: AsyncSession, workspace_id: int, plan: str, sub_end: datetime | None) -> Workspace:
    ws = await get_workspace(session, workspace_id)
    if ws is None:
        raise ValueError("Рабочее пространство не найдено")
    ws.plan = plan
    ws.sub_end = sub_end
    return ws


async def get_workspace_member_count(session: AsyncSession, workspace_id: int) -> int:
    result = await session.execute(
        select(User).where(User.workspace_id == workspace_id)
    )
    return len(result.scalars().all())


# ── Пользователи ──────────────────────────────────────────────────────────────

async def get_user(session, user_id):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(session, workspace_id: int | None = None):
    q = select(User).order_by(User.username)
    if workspace_id is not None:
        q = q.where(User.workspace_id == workspace_id)
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_or_create_user(session, user_id, username, admin_ids=None):
    user = await get_user(session, user_id)
    if user is None:
        role = "admin" if (admin_ids and user_id in admin_ids) else "junior"
        user = User(id=user_id, username=username, role=role)
        session.add(user)
        await session.flush()
        logger.info("Новый пользователь: %s (роль: %s)", user.display_name, role)
    else:
        if user.username != username:
            user.username = username
    return user


async def set_user_workspace(session, user_id: int, workspace_id: int, role: str = "user") -> User:
    user = await get_user(session, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")
    user.workspace_id = workspace_id
    user.role = role
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


# ── ИП ────────────────────────────────────────────────────────────────────────

async def create_ip(session, name, bank_balance=0, cash_balance=0, workspace_id: int | None = None):
    ip = IP(
        name=name,
        workspace_id=workspace_id,
        bank_balance=bank_balance,
        debit_balance=0,
        cash_balance=cash_balance,
        initial_capital=bank_balance + cash_balance,
    )
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


async def get_ip_by_name(session, name, workspace_id: int | None = None):
    q = select(IP).where(IP.name == name)
    if workspace_id is not None:
        q = q.where(IP.workspace_id == workspace_id)
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def get_all_ips(session, workspace_id: int | None = None):
    q = select(IP).order_by(IP.name)
    if workspace_id is not None:
        q = q.where(IP.workspace_id == workspace_id)
    result = await session.execute(q)
    return list(result.scalars().all())


async def count_ips(session, workspace_id: int) -> int:
    result = await session.execute(select(IP).where(IP.workspace_id == workspace_id))
    return len(result.scalars().all())


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


# ── Транзакции ────────────────────────────────────────────────────────────────

async def create_transaction(session, user_id, tx_type, amount, ip_id=None, comment=None,
                              destination=None, workspace_id: int | None = None):
    tx = Transaction(
        user_id=user_id, ip_id=ip_id, workspace_id=workspace_id,
        type=tx_type, amount=amount, comment=comment, destination=destination,
    )
    session.add(tx)
    await session.flush()
    return tx


async def get_transactions(session, *, user_id=None, ip_id=None, since=None, limit=100,
                            include_cancelled=False, workspace_id: int | None = None):
    query = (
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.ip))
        .order_by(Transaction.created_at.desc())
    )
    conditions = []
    if workspace_id is not None:
        conditions.append(Transaction.workspace_id == workspace_id)
    if user_id is not None:
        conditions.append(Transaction.user_id == user_id)
    if ip_id is not None:
        conditions.append(Transaction.ip_id == ip_id)
    if since is not None:
        conditions.append(Transaction.created_at >= since)
    if not include_cancelled:
        conditions.append(Transaction.is_cancelled.is_(False))
    if conditions:
        query = query.where(and_(*conditions))
    query = query.limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_transaction(session, tx_id: int):
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.user), selectinload(Transaction.ip))
        .where(Transaction.id == tx_id)
    )
    return result.scalar_one_or_none()


# ── Долги между ИП ────────────────────────────────────────────────────────────

async def create_ip_debt(session, creditor_ip_id, debtor_ip_id, amount, workspace_id: int | None = None):
    debt = IpDebt(
        creditor_ip_id=creditor_ip_id,
        debtor_ip_id=debtor_ip_id,
        amount=amount,
        workspace_id=workspace_id,
    )
    session.add(debt)
    await session.flush()
    return debt


async def get_active_ip_debts(session, workspace_id: int | None = None):
    q = (
        select(IpDebt)
        .options(selectinload(IpDebt.creditor_ip), selectinload(IpDebt.debtor_ip))
        .where(IpDebt.is_paid.is_(False))
        .order_by(IpDebt.created_at.desc())
    )
    if workspace_id is not None:
        q = q.where(IpDebt.workspace_id == workspace_id)
    result = await session.execute(q)
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


# ── Расходы ───────────────────────────────────────────────────────────────────

async def create_expense(session, user_id: int, description: str, amount: int,
                          workspace_id: int | None = None) -> Expense:
    expense = Expense(user_id=user_id, description=description, amount=amount, workspace_id=workspace_id)
    session.add(expense)
    await session.flush()
    return expense


async def get_expenses(session, limit: int = 100, workspace_id: int | None = None) -> list[Expense]:
    q = select(Expense).order_by(Expense.created_at.desc()).limit(limit)
    if workspace_id is not None:
        q = q.where(Expense.workspace_id == workspace_id)
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_expense(session, expense_id: int):
    result = await session.execute(select(Expense).where(Expense.id == expense_id))
    return result.scalar_one_or_none()


async def get_writeoffs_for_expense(session, expense_id: int) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.ip))
        .where(Transaction.expense_id == expense_id, Transaction.is_cancelled.is_(False))
        .order_by(Transaction.created_at.asc())
    )
    return list(result.scalars().all())


async def delete_expense(session, expense_id: int) -> None:
    expense = await get_expense(session, expense_id)
    if expense is None:
        raise ValueError(f"Расход {expense_id} не найден")
    await session.delete(expense)


async def reset_all_data(session: AsyncSession, workspace_id: int | None = None) -> None:
    """Удаляет все ИП, транзакции, долги, расходы воркспейса."""
    from sqlalchemy import select as sa_select
    if workspace_id is not None:
        # Получаем id всех ИП воркспейса, чтобы удалить транзакции с NULL workspace_id
        ip_ids_result = await session.execute(sa_select(IP.id).where(IP.workspace_id == workspace_id))
        ip_ids = [r[0] for r in ip_ids_result.all()]

        await session.execute(delete(IpDebt).where(IpDebt.workspace_id == workspace_id))

        # Удаляем транзакции по workspace_id ИЛИ по ip_id (для старых записей с NULL workspace_id)
        if ip_ids:
            await session.execute(delete(Transaction).where(
                or_(Transaction.workspace_id == workspace_id, Transaction.ip_id.in_(ip_ids))
            ))
        else:
            await session.execute(delete(Transaction).where(Transaction.workspace_id == workspace_id))

        await session.execute(delete(Expense).where(Expense.workspace_id == workspace_id))
        await session.execute(delete(IP).where(IP.workspace_id == workspace_id))
        users = await get_all_users(session, workspace_id=workspace_id)
    else:
        await session.execute(delete(IpDebt))
        await session.execute(delete(Transaction))
        await session.execute(delete(Expense))
        await session.execute(delete(IP))
        users = await get_all_users(session)
    for u in users:
        u.cash_balance = 0
    logger.info("Все данные сброшены (workspace=%s)", workspace_id)


# ── Глобальная статистика (для создателя бота) ────────────────────────────────

async def get_global_stats(session: AsyncSession) -> dict:
    from sqlalchemy import func as sa_func
    from datetime import timezone

    total_users = (await session.execute(select(sa_func.count(User.id)))).scalar() or 0
    total_workspaces = (await session.execute(select(sa_func.count(Workspace.id)))).scalar() or 0

    plan_counts: dict[str, int] = {}
    rows = (await session.execute(select(Workspace.plan, sa_func.count(Workspace.id)).group_by(Workspace.plan))).all()
    for plan, cnt in rows:
        plan_counts[plan] = cnt

    now = datetime.now(timezone.utc)
    active_subs = (await session.execute(
        select(sa_func.count(Workspace.id)).where(
            Workspace.plan != "free",
            Workspace.sub_end > now,
        )
    )).scalar() or 0

    total_txs = (await session.execute(select(sa_func.count(Transaction.id)))).scalar() or 0
    total_ips = (await session.execute(select(sa_func.count(IP.id)))).scalar() or 0

    return {
        "total_users": total_users,
        "total_workspaces": total_workspaces,
        "plan_counts": plan_counts,
        "active_subs": active_subs,
        "total_transactions": total_txs,
        "total_ips": total_ips,
    }
