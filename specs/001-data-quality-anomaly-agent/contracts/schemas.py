"""
Shared Pydantic v2 schemas — contract source of truth.

These models mirror contracts/api.yaml and are the canonical Python
definitions used by backend/app/models/. Any change here MUST be
reflected in api.yaml and vice versa (they are kept in sync manually
until a code-generation pipeline is added).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, UUID4


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    session_id: UUID4
    filename: str
    row_count: int = Field(ge=1, le=10_000)
    column_count: int = Field(ge=1)
    encoding: str
    parse_warnings: list[str] = []


# ---------------------------------------------------------------------------
# Column Profile
# ---------------------------------------------------------------------------

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
    top_values: list[TopValue] = Field(max_length=10)

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
    example_values: list[str] = Field(max_length=5)
    stats: ColumnStats = None


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

IssueFamilyType = Literal["missing", "duplicate", "outlier", "inconsistent"]
SeverityType = Literal["info", "warning", "error"]

class Finding(BaseModel):
    finding_id: UUID4
    issue_family: IssueFamilyType
    affected_columns: list[str]
    affected_row_indices: list[int]
    severity: SeverityType
    detection_methods: list[str]
    example_rows: list[dict] = Field(max_length=5)
    metadata: dict = {}
    is_resolved: bool = False


# ---------------------------------------------------------------------------
# Quality Score
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Explanation & MCP Blueprints
# ---------------------------------------------------------------------------

OperationHintType = Literal[
    "trim_whitespace", "case_normalization",
    "map_category", "fill_missing", "review_only"
]

RiskLevelType = Literal["low", "medium", "high"]

class MCPActionBlueprint(BaseModel):
    tool_name: str
    parameters: dict = {}
    business_summary: str
    risk_level: RiskLevelType = "low"
    rollback_action: dict = {}

class PolyglotRegexInfo(BaseModel):
    domain: Literal["phone", "postal_code", "date", "general"]
    target_locales: list[str] = []
    regex_pattern: str
    description: str

class Explanation(BaseModel):
    finding_id: str
    is_ai_generated: bool
    explanation_text: str
    business_impact: str
    recommended_action: str
    recommended_regex: Optional[str] = None
    polyglot_regex: Optional[PolyglotRegexInfo] = None
    mcp_action: Optional[MCPActionBlueprint] = None
    operation_hint: OperationHintType
    requires_approval: Literal[True] = True
    generated_at: datetime


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

OperationType = Literal[
    "trim_whitespace", "case_normalization",
    "map_category", "fill_missing", "mark_for_review"
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
    risk_level: RiskLevelType = "low"
    affected_columns: list[str]
    affected_row_indices: list[int]
    preview_diff: Optional[list[CellDiff]] = None
    approval_status: ApprovalStatus = "pending"
    applied_at: Optional[datetime] = None
    original_values: Optional[dict] = None


# ---------------------------------------------------------------------------
# Transformation Log
# ---------------------------------------------------------------------------

class TransformationLog(BaseModel):
    session_id: str
    entries: list[CleaningOperation]  # only approved operations
    exported_at: datetime


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = {}
