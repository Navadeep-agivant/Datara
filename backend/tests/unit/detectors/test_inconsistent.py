import pytest
import pandas as pd
from app.detectors.inconsistent import InconsistentValueDetector

def test_inconsistent_value_detector():
    df = pd.DataFrame({
        "city": ["Mumbai", "mumbai", "MUMBAI", "mumb ai", "Delhi", "Delhi", "Pune"]
    })
    detector = InconsistentValueDetector(threshold=80)
    findings = detector.detect(df)
    
    assert len(findings) > 0
    f = next((item for item in findings if "city" in item.affected_columns), None)
    assert f is not None
    assert f.metadata["canonical_candidate"] in ("Mumbai", "mumbai", "MUMBAI")
    assert len(f.affected_row_indices) > 0
