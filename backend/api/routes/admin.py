"""Административные маршруты: пользователи и ИП."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.ip_manager import create_ip as svc_create_ip

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

    async with session.begin():
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


class IpRequest(BaseModel):
    name: str
    initial_capital: int


@router.post("/ips")
async def create_ip(
    body: IpRequest,
    _admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Создать новое ИП."""
    try:
        ip = await svc_create_ip(session, body.name.strip(), body.initial_capital)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": ip.id, "name": ip.name, "bank_balance": ip.bank_balance}
