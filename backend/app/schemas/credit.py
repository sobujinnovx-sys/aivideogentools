from pydantic import BaseModel


class CreditBalanceResponse(BaseModel):
    credits: int


class CreditTransactionResponse(BaseModel):
    id: str
    amount: int
    type: str
    description: str
    created_at: str

    class Config:
        from_attributes = True


class CreditHistoryResponse(BaseModel):
    transactions: list[CreditTransactionResponse]
    total: int


class PurchaseRequest(BaseModel):
    amount: int  # number of credits to buy
