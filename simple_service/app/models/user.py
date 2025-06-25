from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class Users(SQLModel, table=True):
    user_id: int = Field(default=None, primary_key=True)
    username: str = Field(sa_column_kwargs={'unique': True}, nullable=False)
    email: EmailStr = Field(sa_column_kwargs={'unique': True}, nullable=False)
    password: str = Field(nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    balance: float = Field(default=0.0, nullable=False)
