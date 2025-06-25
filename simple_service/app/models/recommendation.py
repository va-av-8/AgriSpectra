from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class DamageType(str, Enum):
    GROWTH = "G"
    DROUGHT = "DR"
    WEED = "WD"


class GrowthStage(str, Enum):
    FLOWERING = "F"
    MATURITY = "M"
    SOWING = "S"
    VEGETATIVE = "V"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(SQLModel, table=True):
    __tablename__ = "recommendations"

    id: Optional[int] = Field(default=None, primary_key=True)
    damage_type: DamageType = Field(
        sa_column_kwargs={"nullable": False, "comment": "Тип повреждения"}
    )
    growth_stage: GrowthStage = Field(
        sa_column_kwargs={"nullable": False, "comment": "Стадия роста культуры"}
    )
    severity: SeverityLevel = Field(
        sa_column_kwargs={"nullable": False, "comment": "Степень тяжести повреждения"}
    )
    recommendation: str = Field(
        sa_column_kwargs={"nullable": False, "comment": "Текст рекомендации по уходу"}
    )
    source: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"nullable": True, "comment": "Источник (агро-экспертная литература или URL)"}
    )
