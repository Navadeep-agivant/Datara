import pytest
import pandas as pd
import uuid
from app.models.finding import Finding
from app.services.scorer import calculate_quality_scores

def test_calculate_quality_scores():
    df = pd.DataFrame({"col_a": range(100), "col_b": range(100)})
    finding = Finding(
        finding_id=uuid.uuid4(),
        issue_family="missing",
        affected_columns=["col_a"],
        affected_row_indices=list(range(10)), # 10% missing
        severity="error",
        detection_methods=["sentinel_check"],
        example_rows=[]
    )
    score_res = calculate_quality_scores(df, [finding])
    assert score_res.overall_score < 100.0
    col_a_score = next(c for c in score_res.column_scores if c.column_name == "col_a")
    assert col_a_score.score == 90.0 # 100 - 10.0
    col_b_score = next(c for c in score_res.column_scores if c.column_name == "col_b")
    assert col_b_score.score == 100.0
