import pytest
import pandas as pd
from app.detectors.duplicates import DuplicateDetector

def test_duplicate_detector():
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-1", "ORD-3", "ORD-4"],
        "customer": ["Alice", "Bob", "Alice", "Charlie", "Dave"],
        "amount": [100.0, 200.0, 100.0, 300.0, 400.0]
    })
    detector = DuplicateDetector()
    findings = detector.detect(df)
    
    # Exact duplicate rows exist (row 0 and row 2)
    exact_finding = next((f for f in findings if f.metadata.get("match_type") == "exact"), None)
    assert exact_finding is not None
    assert 0 in exact_finding.affected_row_indices
    assert 2 in exact_finding.affected_row_indices
