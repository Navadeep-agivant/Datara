from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, UUID4

OperationType = Literal[
    "trim_whitespace", "case_normalization",
    "map_category", "fill_missing", "mark_for_review",
    "recalculate_arithmetic", "drop_exact_duplicate"
]

ApprovalStatus = Literal["pending", "approved", "rejected"]

class CellDiff(BaseModel):
    row_index: int
    column_name: str
    before: str
    after: str

class CleaningOperation(BaseModel):
    operation_id: UUID4
    finding_id: str
    operation_type: OperationType
    risk_level: Literal["low", "medium", "high"] = "low"
    affected_columns: list[str]
    affected_row_indices: list[int]
    preview_diff: Optional[list[CellDiff]] = None
    pandas_code: Optional[str] = None
    bucket: Literal["auto_fixable", "needs_review"] = "auto_fixable"
    approval_status: ApprovalStatus = "pending"
    applied_at: Optional[datetime] = None
    original_values: Optional[dict] = None
