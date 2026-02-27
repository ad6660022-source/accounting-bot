"""Административные маршруты: пользователи и ИП."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.ip_manager import create_ip as svc_create_ip
from backend.services.ip_manager import update_ip_balances as svc_update_ip_balances

router = APIRouter()


# ── Пользователи ──────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    _admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    """Список всех зарегистрированных пользователей."""
    users = await crud.get_all_users(session)
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "role": u.role,
            "cash_balance": u.cash_balance,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


class RoleRequest(BaseModel):
    role: str  # "admin" или "user"


@router.patch("/users/{user_id}/role")
async def set_role(
    user_id: int,
    body: RoleRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Изменить роль пользователя."""
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=422, detail="Роль должна быть 'admin' или 'user'")
    if user_id == admin.id and body.role == "user":
        raise HTTPException(status_code=400, detail="Нельзя снять права с самого себя")

    user = await crud.set_user_role(session, user_id, body.role)
    return {"id": user.id, "role": user.role}


# ── ИП ───────────────────────────────────────────────────────────────────────

@router.get("/ips")
async def list_ips(
    _admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    """Все ИП."""
    ips = await crud.get_all_ips(session)
    return [
        {
            "id": ip.id,
            "name": ip.name,
            "bank_balance": ip.bank_balance,
            "cash_balance": ip.cash_balance,
            "initial_capital": ip.initial_capital,
        }
        for ip in ips
    ]


class IpCreateRequest(BaseModel):
    name: str
    bank_balance: int = 0
    cash_balance: int = 0


@router.post("/ips")
async def create_ip(
    body: IpCreateRequest,
    _admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Создать новое ИП."""
    try:
        ip = await svc_create_ip(
            session,
            body.name.strip(),
            bank_balance=body.bank_balance,
            cash_balance=body.cash_balance,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": ip.id, "name": ip.name, "bank_balance": ip.bank_balance, "cash_balance": ip.cash_balance}


class IpBalancesRequest(BaseModel):
    bank_balance: int
    cash_balance: int


@router.patch("/ips/{ip_id}/balances")
async def update_ip_balances(
    ip_id: int,
    body: IpBalancesRequest,
    _admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Скорректировать остатки ИП (Р/С и наличка)."""
    try:
        ip = await svc_update_ip_balances(
            session, ip_id,
            bank_balance=body.bank_balance,
            cash_balance=body.cash_balance,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"id": ip.id, "name": ip.name, "bank_balance": ip.bank_balance, "cash_balance": ip.cash_balance}
