from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from pydantic import BaseModel
from typing import Dict, Optional, Any
from sqlalchemy.dialects.postgresql import JSON


class Predictions(SQLModel, table=True):
    prediction_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", nullable=False)
    model_id: int = Field(foreign_key="models.model_id", nullable=True)
    # task_id: int = Field(foreign_key="mltasks.task_id")
    input_photo_url: str
    input_data: str
    prediction_result: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False)
    )
    cost: float
    timestamp: datetime = datetime.now(timezone.utc)

    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    model_id: int
    image_id: Optional[int] = None


class PredictionResponse(BaseModel):
    task_id: int
    cost: float
    message: str
