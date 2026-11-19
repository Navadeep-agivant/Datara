# Data Model: AI Data Quality & Anomaly Detection Agent

**Phase**: 1 — Design & Contracts  
**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Last Updated**: 2026-11-19 (Aligned with Constitution v1.3.0)

---

## Core Domain Entities

### 1. Finding
Emitted by Tier 1 detectors, rule-based validity validators, and adaptive synthesizers:
```python
IssueFamilyType = Literal[
    "missing", "duplicate", "outlier", "inconsistent", 
    "arithmetic_conflict", "invalid", "novel_anomaly"
]
SeverityType = Literal["info", "warning", "error"]

class Finding(BaseModel):
    finding_id: UUID
    issue_family: IssueFamilyType
    affected_columns: list[str]
    affected_row_indices: list[int]
    severity: SeverityType
    detection_methods: list[str]
    example_rows: list[dict] # Sanitized of NaN/inf for JSON compliance
    metadata: dict           # Relational 3-tier key details, canonical candidates, bounds
    is_resolved: bool = False
```

### 2. Explanation (Tier 2 Cognitive Layer)
Augmented by the LLM or deterministic fallback:
```python
class MCPActionBlueprint(BaseModel):
    tool_name: str
    parameters: dict
    business_summary: str
    risk_level: Literal["low", "medium", "high"]
    rollback_action: dict

class PolyglotRegexInfo(BaseModel):
    domain: Literal["phone", "postal_code", "date", "general"]
    target_locales: list[str]
    regex_pattern: str
    description: str

class Explanation(BaseModel):
    finding_id: str
    is_ai_generated: bool
    explanation_text: str       # Non-technical explanation
    business_impact: str        # Impact on KPI, metrics, reporting
    recommended_action: str     # Actionable remediation proposal
    recommended_regex: Optional[str] = None # Polyglot regex pattern
    polyglot_regex: Optional[PolyglotRegexInfo] = None # Structured Core Triad metadata
    mcp_action: Optional[MCPActionBlueprint] = None    # MCP tool action blueprint
    pandas_code: Optional[str] = None                  # Mandatory executable code
    operation_hint: Literal["trim_whitespace", "case_normalization", "map_category", "fill_missing", "review_only"]
    requires_approval: Literal[True] = True
    generated_at: datetime
```

### 3. CleaningOperation & CellDiff (Visual Sandbox Entity)
Tracks reversible data transformations and executable code:
```python
class CellDiff(BaseModel):
    row_index: int
    column_name: str
    before: str
    after: str

class CleaningOperation(BaseModel):
    operation_id: UUID
    finding_id: str
    operation_type: Literal[
        "trim_whitespace", "case_normalization", "map_category", 
        "fill_missing", "mark_for_review", "recalculate_arithmetic", 
        "drop_exact_duplicate"
    ]
    risk_level: Literal["low", "medium", "high"] = "low"
    bucket: Literal["auto_fixable", "needs_review"] = "auto_fixable"
    affected_columns: list[str]
    affected_row_indices: list[int]
    preview_diff: Optional[list[CellDiff]] = None
    pandas_code: Optional[str] = None # Mandatory executable transformation code
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    applied_at: Optional[datetime] = None
    original_values: Optional[dict] = None # Preserved for instant LIFO undo
```

### 4. DatasetQualityScore & Calibrated Weights
```python
class ScoreDeduction(BaseModel):
    issue_family: str
    severity: str
    affected_pct: float
    points_deducted: float

class ColumnScore(BaseModel):
    column_name: str
    score: float # 0.0 - 100.0
    deductions: list[ScoreDeduction] = []

class DatasetQualityScore(BaseModel):
    overall_score: float # 0.0 - 100.0
    column_scores: list[ColumnScore]
    computed_at: datetime
    weights_table: dict[str, float] = {}
```

### 5. SynthesizedRule (Adaptive Self-Evolving Engine)
Persisted in the dynamic detector registry for continuous learning:
```python
class SynthesizedRule(BaseModel):
    rule_id: str
    rule_name: str
    target_columns: list[str]
    anomaly_pattern: str       # Regex or python validation condition
    explanation: str
    severity: Literal["info", "warning", "error"]
    sample_violations: list[str]
    remediation_code: str       # Executable pandas snippet
    created_at: datetime
    is_active: bool = True
```
