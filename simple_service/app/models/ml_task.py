from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSON


class MLTasks(SQLModel, table=True):
    title: Optional[str]
    task_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", nullable=False)
    model_id: int = Field(foreign_key="models.model_id", nullable=False)
    prediction_id: int = Field(foreign_key="predictions.prediction_id", nullable=True)
    input_data: str
    prediction_result: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=True)
    )
    task_status: str
    timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self):
        return self.model_dump()

    class Config:
        protected_namespaces = ()


class MLTasksUpdate(BaseModel):
    title: Optional[str] = None
    task_id: Optional[int] = None
    user_id: Optional[int] = None
    model_id: Optional[int] = None
    prediction_id: int
    input_data: Optional[str] = None
    prediction_result: Optional[str] = None
    task_status: str
    timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self):
        return self.model_dump()

    class Config:
        protected_namespaces = ()
