"""
Эндпоинты управления расходами.
Создание расходов, списание на счета ИП, удаление.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_current_user, get_regular_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.transaction import InsufficientFundsError, cancel_operation, write_off_expense

router = APIRouter()


class CreateExpenseRequest(BaseModel):
    description: str
    amount: int


class WriteOffRequest(BaseModel):
    ip_id: int
    amount: int
    source: str  # cash / bank / debit


@router.get("/expenses")
async def list_expenses(
    limit: int = 100,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    expenses = await crud.get_expenses(session, limit=limit)
    result = []
    for exp in expenses:
        writeoffs = await crud.get_writeoffs_for_expense(session, exp.id)
        result.append({
            "id": exp.id,
            "description": exp.description,
            "amount": exp.amount,
            "is_closed": exp.is_closed,
            "created_at": exp.created_at.isoformat(),
            "writeoffs": [
                {
                    "tx_id": w.id,
                    "ip_id": w.ip_id,
                    "ip_name": w.ip.name if w.ip else None,
                    "amount": w.amount,
                    "source": w.destination or "cash",
                }
                for w in writeoffs
            ],
        })
    return result


@router.post("/expenses")
async def create_expense(
    body: CreateExpenseRequest,
    current_user: User = Depends(get_regular_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not body.description.strip():
        raise HTTPException(status_code=422, detail="Введите описание расхода")
    if body.amount <= 0:
        raise HTTPException(status_code=422, detail="Сумма должна быть больше нуля")
    expense = await crud.create_expense(session, current_user.id, body.description.strip(), body.amount)
    return {"id": expense.id, "description": expense.description, "amount": expense.amount}


@router.post("/expenses/{expense_id}/writeoffs")
async def write_off(
    expense_id: int,
    body: WriteOffRequest,
    current_user: User = Depends(get_regular_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if body.source not in ("cash", "bank", "debit"):
        raise HTTPException(status_code=422, detail="Источник должен быть cash, bank или debit")
    try:
        tx = await write_off_expense(
            session,
            expense_id=expense_id,
            ip_id=body.ip_id,
            amount=body.amount,
            source=body.source,
            user_id=current_user.id,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, "transaction_id": tx.id}


@router.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: int,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Отменяет все списания расхода (возврат балансов) и удаляет сам расход."""
    expense = await crud.get_expense(session, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Расход не найден")

    # Отменяем все активные списания — балансы ИП восстанавливаются
    writeoffs = await crud.get_writeoffs_for_expense(session, expense_id)
    for tx in writeoffs:
        try:
            await cancel_operation(session, tx.id, admin.id)
        except ValueError:
            pass  # уже отменена

    # Удаляем запись расхода
    await crud.delete_expense(session, expense_id)
    return {"success": True}


@router.patch("/expenses/{expense_id}/close")
async def close_expense(
    expense_id: int,
    current_user: User = Depends(get_regular_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Помечает расход как закрытый (без отмены списаний)."""
    expense = await crud.get_expense(session, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Расход не найден")
    expense.is_closed = True
    return {"success": True}
