from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user, get_session
from backend.database import crud
from backend.database.models import TX_LABELS, User
from backend.services.transaction import InsufficientFundsError, process_operation

router = APIRouter()


class OperationRequest(BaseModel):
    op_type: str
    amount: int
    ip_id: Optional[int] = None
    target_ip_id: Optional[int] = None
    comment: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v


@router.post("/operations")
async def create_operation(
    body: OperationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        tx = await process_operation(
            session,
            user_id=current_user.id,
            op_type=body.op_type,
            amount=body.amount,
            ip_id=body.ip_id,
            target_ip_id=body.target_ip_id,
            comment=body.comment,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, "transaction_id": tx.id}


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    txs = await crud.get_transactions(session, user_id=current_user.id, limit=limit)
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "type_label": TX_LABELS.get(tx.type, tx.type),
            "amount": tx.amount,
            "ip_name": tx.ip.name if tx.ip else None,
            "comment": tx.comment,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in txs
    ]
