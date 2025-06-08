from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class UserImages(SQLModel, table=True):
    image_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", nullable=False)
    # task_id: int = Field(foreign_key="mltasks.task_id")
    image_url: str
    internal_url: str
    input_data: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="When this image record was created"
    )

    class Config:
        protected_namespaces = ()