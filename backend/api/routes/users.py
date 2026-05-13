"""Публичный список пользователей воркспейса."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session, get_workspace_id
from backend.database import crud
from backend.database.models import User

router = APIRouter()


@router.get("/users")
async def list_users_public(
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_workspace_id),
    session: AsyncSession = Depends(get_session),
) -> list:
    users = await crud.get_all_users(session, workspace_id=workspace_id)
    return [
        {"id": u.id, "display_name": u.display_name}
        for u in users
        if u.id != current_user.id
    ]
