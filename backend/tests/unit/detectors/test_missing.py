import pytest
import pandas as pd
from app.detectors.missing import MissingValueDetector

def test_missing_value_detector():
    df = pd.DataFrame({
        "col_a": ["val1", "", "None", "val2"],
        "col_b": [1, None, 3, 4],
        "col_c": ["N/A", "test", "-", "Unknown"]
    })
    detector = MissingValueDetector()
    findings = detector.detect(df)
    
    # Expect findings for col_a, col_b, col_c
    cols_with_missing = {col for f in findings for col in f.affected_columns}
    assert "col_a" in cols_with_missing
    assert "col_b" in cols_with_missing
    assert "col_c" in cols_with_missing
    
    # Verify metadata contains null count
    finding_b = next(f for f in findings if "col_b" in f.affected_columns)
    assert finding_b.metadata["null_count"] == 1
    assert finding_b.severity == "warning" or finding_b.severity == "error"
