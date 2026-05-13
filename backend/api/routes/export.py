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
from backend.services.export import generate_excel

router = APIRouter()


@router.get("/export")
async def export_excel(
    ip_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    workspace_id: int = Depends(get_workspace_id),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    ip = await crud.get_ip(session, ip_id)
    if ip is None:
        raise HTTPException(status_code=404, detail="ИП не найдено")

    all_txs = await crud.get_transactions(session, ip_id=ip_id, limit=10000, workspace_id=workspace_id)

    excel_bytes = generate_excel(ip, all_txs, date_from=date_from, date_to=date_to)

    today = date.today().strftime("%Y-%m-%d")
    filename = f"{ip.name}_{today}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
