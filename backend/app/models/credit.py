import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransactionType(str, PyEnum):
    DEBIT = "debit"
    REFUND = "refund"
    PURCHASE = "purchase"
    BONUS = "bonus"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    description: Mapped[str] = mapped_column(Text, default="")
    job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="credit_transactions")  # noqa: F821
