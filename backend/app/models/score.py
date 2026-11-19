from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

class ScoreDeduction(BaseModel):
    issue_family: str
    severity: str
    affected_pct: float
    points_deducted: float

class ColumnScore(BaseModel):
    column_name: str
    score: float = Field(ge=0.0, le=100.0)
    deductions: list[ScoreDeduction] = []

class DatasetQualityScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    column_scores: list[ColumnScore]
    computed_at: datetime
    weights_table: dict[str, float] = Field(default_factory=dict)
