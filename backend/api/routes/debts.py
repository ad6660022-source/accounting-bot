from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import User
from backend.services.transaction import InsufficientFundsError, repay_ip_debt_operation

router = APIRouter()


@router.get("/debts")
async def get_ip_debts(
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    debts = await crud.get_active_ip_debts(session)
    return [
        {
            "id": d.id,
            "creditor_ip_id": d.creditor_ip_id,
            "creditor_ip_name": d.creditor_ip.name,
            "debtor_ip_id": d.debtor_ip_id,
            "debtor_ip_name": d.debtor_ip.name,
            "amount": d.amount,
            "created_at": d.created_at.isoformat(),
        }
        for d in debts
    ]


class RepayRequest(BaseModel):
    amount: int


@router.post("/debts/{debt_id}/repay")
async def repay_ip_debt(
    debt_id: int,
    body: RepayRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        await repay_ip_debt_operation(session, debt_id=debt_id, amount=body.amount, user_id=current_user.id)
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True}
