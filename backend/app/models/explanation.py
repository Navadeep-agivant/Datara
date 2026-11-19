from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field

OperationHintType = Literal[
    "trim_whitespace", "case_normalization",
    "map_category", "fill_missing", "review_only"
]

RiskLevelType = Literal["low", "medium", "high"]

class MCPActionBlueprint(BaseModel):
    tool_name: str
    parameters: Dict = Field(default_factory=dict)
    business_summary: str
    risk_level: RiskLevelType = "low"
    rollback_action: Dict = Field(default_factory=dict)

class PolyglotRegexInfo(BaseModel):
    domain: Literal["phone", "postal_code", "date", "general"]
    target_locales: List[str] = Field(default_factory=list)
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
    pandas_code: Optional[str] = None
    operation_hint: OperationHintType
    requires_approval: Literal[True] = True
    generated_at: datetime
