from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_admin_user, get_current_user, get_regular_user, get_session
from backend.database import crud
from backend.database.models import TX_LABELS, User
from backend.services.transaction import InsufficientFundsError, cancel_operation, edit_operation, process_operation

router = APIRouter()


class OperationRequest(BaseModel):
    op_type: str
    amount: int
    ip_id: Optional[int] = None
    target_ip_id: Optional[int] = None
    comment: Optional[str] = None
    destination: Optional[str] = None  # cash / bank / debit (для приходов)

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v


class EditOperationRequest(BaseModel):
    amount: Optional[int] = None
    comment: Optional[str] = None


@router.post("/operations")
async def create_operation(
    body: OperationRequest,
    current_user: User = Depends(get_regular_user),
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
            destination=body.destination,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, "transaction_id": tx.id}


@router.post("/operations/{tx_id}/cancel")
async def cancel_operation_route(
    tx_id: int,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        tx = await cancel_operation(session, tx_id, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, "transaction_id": tx.id}


@router.patch("/operations/{tx_id}")
async def edit_operation_route(
    tx_id: int,
    body: EditOperationRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        tx = await edit_operation(
            session,
            tx_id=tx_id,
            admin_id=admin.id,
            new_amount=body.amount,
            new_comment=body.comment,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, "transaction_id": tx.id, "amount": tx.amount, "comment": tx.comment}


@router.get("/transactions")
async def get_transactions(
    limit: int = 100,
    ip_id: Optional[int] = None,
    include_cancelled: bool = False,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    txs = await crud.get_transactions(session, ip_id=ip_id, limit=limit, include_cancelled=include_cancelled)
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "type_label": TX_LABELS.get(tx.type, tx.type),
            "amount": tx.amount,
            "ip_id": tx.ip_id,
            "ip_name": tx.ip.name if tx.ip else None,
            "user_name": tx.user.display_name if tx.user else None,
            "comment": tx.comment,
            "is_cancelled": tx.is_cancelled,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in txs
    ]
