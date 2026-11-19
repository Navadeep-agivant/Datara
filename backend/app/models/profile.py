from __future__ import annotations
from datetime import datetime
from typing import Literal, Union, Optional
from pydantic import BaseModel, Field

class TopValue(BaseModel):
    value: str
    count: int

class NumericStats(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std: float
    is_constant: bool

class CategoricalStats(BaseModel):
    top_values: list[TopValue] = Field(default_factory=list, max_length=10)

class DatetimeStats(BaseModel):
    min_date: datetime
    max_date: datetime
    format_detected: str = ""

ColumnStats = Union[NumericStats, CategoricalStats, DatetimeStats, None]
InferredType = Literal["numeric", "categorical", "datetime", "identifier", "text", "unknown"]

class ColumnProfile(BaseModel):
    column_name: str
    inferred_type: InferredType
    total_rows: int
    null_count: int = Field(ge=0)
    null_pct: float = Field(ge=0.0, le=100.0)
    unique_count: int = Field(ge=0)
    example_values: list[str] = Field(default_factory=list, max_length=5)
    stats: Optional[ColumnStats] = None
