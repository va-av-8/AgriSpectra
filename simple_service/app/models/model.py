from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Models(SQLModel, table=True):
    model_id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    description: str = Field(nullable=False)
    cost: float = Field(nullable=False)
    artifact_path: str = Field(nullable=False, description="WandB artifact identifier, e.g. 'entity/project/artifact_name:version'")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="When this model record was created"
    )


# Pydantic-модель для создания новой записи
class ModelArtifactCreate(SQLModel):
    name: str
    description: str
    cost: float
    artifact_path: str


# Pydantic-модель для чтения (response)
class ModelArtifactRead(SQLModel):
    model_id: int
    name: str
    description: str
    cost: float
    artifact_path: str
    created_at: datetime

    class Config:
        orm_mode = True
