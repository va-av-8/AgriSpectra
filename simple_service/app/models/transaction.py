from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class Transactions(SQLModel, table=True):
    transaction_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", nullable=False)
    transaction_type: str
    amount: float
    timestamp: datetime = datetime.now(timezone.utc)


class BalanceUpdate(BaseModel):
    amount: int
