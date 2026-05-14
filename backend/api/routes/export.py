import io
from datetime import date
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_regular_user, get_session, get_workspace_id
from backend.database import crud
from backend.database.models import User
from backend.services.export import generate_excel, generate_workspace_excel

router = APIRouter()


@router.get("/export")
async def export_ip_excel(
    ip_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    workspace_id: int = Depends(get_workspace_id),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Выгрузка по одному ИП."""
    ip = await crud.get_ip(session, ip_id)
    if ip is None:
        raise HTTPException(status_code=404, detail="ИП не найдено")

    all_txs = await crud.get_transactions(session, ip_id=ip_id, limit=10000, workspace_id=workspace_id)
    excel_bytes = generate_excel(ip, all_txs, date_from=date_from, date_to=date_to)

    today = date.today().strftime("%Y-%m-%d")
    filename = f"{ip.name}_{today}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/export/workspace")
async def export_workspace_excel(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_regular_user),
    workspace_id: int = Depends(get_workspace_id),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Полная выгрузка по воркспейсу: все ИП, аналитика, расходы."""
    ips = await crud.get_all_ips(session, workspace_id=workspace_id)
    all_txs = await crud.get_transactions(session, limit=50000, workspace_id=workspace_id)
    expenses = await crud.get_expenses(session, limit=10000, workspace_id=workspace_id)

    # Подгружаем списания для каждого расхода
    for exp in expenses:
        exp.writeoffs = await crud.get_writeoffs_for_expense(session, exp.id)

    excel_bytes = generate_workspace_excel(
        ips=ips,
        all_transactions=all_txs,
        expenses=expenses,
        date_from=date_from,
        date_to=date_to,
    )

    today = date.today().strftime("%Y-%m-%d")
    ws = await crud.get_workspace(session, workspace_id)
    ws_name = ws.name if ws else "workspace"
    filename = f"Отчёт_{ws_name}_{today}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
