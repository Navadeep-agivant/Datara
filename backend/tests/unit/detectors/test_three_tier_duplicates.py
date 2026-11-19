import pandas as pd
import pytest
from app.detectors.duplicates import DuplicateDetector

def test_three_tier_duplicate_classification():
    detector = DuplicateDetector()
    df = pd.DataFrame({
        "order_id": ["ORD-101", "ORD-102", "ORD-101", "ORD-104", "ORD-104", "ORD-105"],
        "order_date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-04", "2024-01-05", "2024-01-06"],
        "customer_name": ["Alice", "Bob", "Alice", "Charlie", "Different Charlie", "Alice"],
        "total_amount": [100.0, 200.0, 100.0, 400.0, 999.0, 150.0]
    })
    # Row 0 and Row 2: Exact duplicate (ORD-101, same date, same customer, same amount) -> Tier A (auto_drop)
    # Row 3 and Row 4: ID Collision (both ORD-104, but differing customer and amount!) -> Tier B (manual_review)
    # Row 0/2 and Row 5: Repeat customer (Alice placed ORD-101 on Jan 1 and ORD-105 on Jan 6) -> Tier C (not_an_issue)

    findings = detector.detect(df, primary_key="order_id", entity_key="customer_name")
    
    tier_a = [f for f in findings if f.metadata.get("tier") == "tier_a" or f.metadata.get("classification") == "exact_duplicate"]
    tier_b = [f for f in findings if f.metadata.get("tier") == "tier_b" or f.metadata.get("classification") == "id_collision"]
    tier_c = [f for f in findings if f.metadata.get("tier") == "tier_c" or f.metadata.get("classification") == "repeat_customer"]

    # Assert Tier A: Exact duplicate detected and tagged
    assert len(tier_a) >= 1
    assert 0 in tier_a[0].affected_row_indices
    assert 2 in tier_a[0].affected_row_indices
    assert tier_a[0].metadata.get("action") == "auto_drop"

    # Assert Tier B: ID Collision routed to manual review
    assert len(tier_b) >= 1
    assert 3 in tier_b[0].affected_row_indices
    assert 4 in tier_b[0].affected_row_indices
    assert tier_b[0].metadata.get("action") == "manual_review"

    # Assert Tier C: Repeat customer flagged as "not an issue"
    assert len(tier_c) >= 1
    assert tier_c[0].metadata.get("status") == "not_an_issue"
    assert "Alice" in str(tier_c[0].metadata.get("customer_name") or tier_c[0].metadata)
