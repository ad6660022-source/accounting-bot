"""Информация о текущем пользователе."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import PLAN_LIMITS, User

router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    workspace_info = None
    if current_user.workspace_id:
        ws = await crud.get_workspace(session, current_user.workspace_id)
        if ws:
            workspace_info = {
                "id": ws.id,
                "name": ws.name,
                "plan": ws.plan,
                "plan_label": ws.plan_label,
                "is_owner": ws.owner_id == current_user.id,
                "invite_code": ws.invite_code if ws.owner_id == current_user.id else None,
                "sub_active": ws.is_sub_active,
                "ip_limit": PLAN_LIMITS.get(ws.plan, PLAN_LIMITS["free"])["ips"],
            }
    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "cash_balance": current_user.cash_balance,
        "workspace": workspace_info,
    }
