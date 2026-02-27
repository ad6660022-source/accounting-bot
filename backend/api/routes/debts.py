"""Долги: просмотр и погашение."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.transaction import InsufficientFundsError, repay_debt_operation

router = APIRouter()


@router.get("/debts")
async def get_debts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Долги текущего пользователя."""
    owed_to_me, i_owe = await crud.get_active_debts_for_user(session, current_user.id)
    return {
        "owed_to_me": [
            {
                "id": d.id,
                "debtor_id": d.debtor_id,
                "debtor_name": d.debtor.display_name,
                "amount": d.amount,
            }
            for d in owed_to_me
        ],
        "i_owe": [
            {
                "id": d.id,
                "creditor_id": d.creditor_id,
                "creditor_name": d.creditor.display_name,
                "amount": d.amount,
            }
            for d in i_owe
        ],
    }


class RepayRequest(BaseModel):
    amount: int


@router.post("/debts/{debt_id}/repay")
async def repay_debt(
    debt_id: int,
    body: RepayRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Погасить долг (частично или полностью)."""
    try:
        tx = await repay_debt_operation(
            session,
            debt_id=debt_id,
            payer_id=current_user.id,
            amount=body.amount,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    updated_user = await crud.get_user(session, current_user.id)
    return {"success": True, "new_balance": updated_user.cash_balance}
