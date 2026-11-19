from __future__ import annotations
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

IssueFamilyType = Literal["missing", "duplicate", "outlier", "inconsistent", "arithmetic_conflict", "invalid", "novel_anomaly"]
SeverityType = Literal["info", "warning", "error"]

class Finding(BaseModel):
    finding_id: UUID
    issue_family: IssueFamilyType
    affected_columns: list[str]
    affected_row_indices: list[int]
    severity: SeverityType
    detection_methods: list[str]
    example_rows: list[dict] = Field(default_factory=list, max_length=5)
    metadata: dict = {}
    is_resolved: bool = False
