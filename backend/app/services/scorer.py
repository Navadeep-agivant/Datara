from datetime import datetime, timezone
from typing import List, Dict
import pandas as pd
from app.models.finding import Finding
from app.models.score import DatasetQualityScore, ColumnScore, ScoreDeduction

SCORING_WEIGHTS_TABLE: Dict[str, float] = {
    "arithmetic_conflict": 2.0,
    "invalid": 1.5,
    "missing": 1.0,
    "duplicate": 1.0,
    "inconsistent": 0.5,
    "outlier": 0.5,
    "novel_anomaly": 1.0
}

DEDUCTION_WEIGHTS = {
    ("arithmetic_conflict", "error"): 2.0,
    ("arithmetic_conflict", "warning"): 1.5,
    ("arithmetic_conflict", "info"): 0.5,

    ("invalid", "error"): 1.5,
    ("invalid", "warning"): 1.0,
    ("invalid", "info"): 0.5,

    ("novel_anomaly", "error"): 1.0,
    ("novel_anomaly", "warning"): 0.8,
    ("novel_anomaly", "info"): 0.4,

    ("missing", "error"): 1.0,
    ("missing", "warning"): 0.8,
    ("missing", "info"): 0.4,

    ("duplicate", "error"): 1.0,
    ("duplicate", "warning"): 0.8,
    ("duplicate", "info"): 0.0,

    ("inconsistent", "error"): 0.5,
    ("inconsistent", "warning"): 0.4,
    ("inconsistent", "info"): 0.2,

    ("outlier", "error"): 0.5,
    ("outlier", "warning"): 0.3,
    ("outlier", "info"): 0.1,
}

def calculate_quality_scores(df: pd.DataFrame, findings: List[Finding]) -> DatasetQualityScore:
    total_rows = max(len(df), 1)
    column_deductions: Dict[str, List[ScoreDeduction]] = {col: [] for col in df.columns}

    for finding in findings:
        if finding.is_resolved:
            continue
        # Legitimate repeat customers or marked "not an issue" do not penalize quality score
        if finding.metadata.get("status") == "not_an_issue" or finding.metadata.get("classification") == "repeat_customer":
            continue

        weight = DEDUCTION_WEIGHTS.get((finding.issue_family, finding.severity), 0.5)
        affected_count = len(finding.affected_row_indices)
        affected_pct = round((affected_count / total_rows) * 100, 2)
        points_deducted = round(affected_pct * weight, 2)

        for col in finding.affected_columns:
            if col in column_deductions:
                column_deductions[col].append(ScoreDeduction(
                    issue_family=finding.issue_family,
                    severity=finding.severity,
                    affected_pct=affected_pct,
                    points_deducted=points_deducted
                ))

    col_scores: List[ColumnScore] = []
    for col in df.columns:
        deductions = column_deductions.get(col, [])
        total_deduction = sum(d.points_deducted for d in deductions)
        score = max(0.0, round(100.0 - total_deduction, 2))
        col_scores.append(ColumnScore(
            column_name=col,
            score=score,
            deductions=deductions
        ))

    if col_scores:
        overall = round(sum(cs.score for cs in col_scores) / len(col_scores), 2)
    else:
        overall = 100.0

    return DatasetQualityScore(
        overall_score=overall,
        column_scores=col_scores,
        computed_at=datetime.now(timezone.utc),
        weights_table=SCORING_WEIGHTS_TABLE
    )
