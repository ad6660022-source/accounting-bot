"""
Эндпоинт выгрузки Excel-отчёта по операциям ИП.
Доступен только пользователям с ролью user или admin.
"""

import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_regular_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.export import generate_excel

router = APIRouter()


@router.get("/export")
async def export_excel(
    ip_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    _user: User = Depends(get_regular_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    ip = await crud.get_ip(session, ip_id)
    if ip is None:
        raise HTTPException(status_code=404, detail="ИП не найдено")

    # Загружаем ВСЕ транзакции ИП для корректного вычисления running balance
    all_txs = await crud.get_transactions(session, ip_id=ip_id, limit=10000)

    excel_bytes = generate_excel(ip, all_txs, date_from=date_from, date_to=date_to)

    today = date.today().strftime("%Y-%m-%d")
    safe_name = ip.name.replace(" ", "_")
    filename = f"{safe_name}_{today}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
