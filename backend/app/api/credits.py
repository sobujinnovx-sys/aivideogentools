from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.credit import CreditTransaction, TransactionType
from app.schemas.credit import CreditBalanceResponse, CreditTransactionResponse, CreditHistoryResponse

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return CreditBalanceResponse(credits=user.credits)


@router.get("/history", response_model=CreditHistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    count_result = await db.execute(
        select(func.count(CreditTransaction.id)).where(CreditTransaction.user_id == user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()

    return CreditHistoryResponse(
        transactions=[
            CreditTransactionResponse(
                id=t.id,
                amount=t.amount,
                type=t.type.value,
                description=t.description,
                created_at=t.created_at.isoformat(),
            )
            for t in transactions
        ],
        total=total,
    )


@router.post("/bonus")
async def claim_bonus(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == user.id,
            CreditTransaction.type == TransactionType.BONUS,
        )
    )
    if result.scalar_one_or_none():
        return {"message": "Bonus already claimed"}

    user.credits += 50
    db.add(CreditTransaction(
        user_id=user.id,
        amount=50,
        type=TransactionType.BONUS,
        description="Welcome bonus",
    ))
    return {"message": "50 bonus credits added", "credits": user.credits}
