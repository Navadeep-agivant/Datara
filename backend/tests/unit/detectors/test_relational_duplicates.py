import pandas as pd
from app.detectors.duplicates import DuplicateDetector

def test_relational_deduplication_preserves_repeat_orders():
    # Customer 'Alice' ordered on two different dates with different order_ids
    # Customer 'Bob' has an exact duplicate row
    # Order 'ORD99' has conflicting items with identical order_id
    data = {
        "order_id": ["ORD001", "ORD002", "ORD003", "ORD003", "ORD99", "ORD99"],
        "customer_name": ["Alice Smith", "Alice Smith", "Bob Jones", "Bob Jones", "Charlie Brown", "Charlie Brown"],
        "order_date": ["2026-01-10", "2026-02-15", "2026-01-12", "2026-01-12", "2026-03-01", "2026-03-01"],
        "product": ["Widget A", "Widget B", "Gadget X", "Gadget X", "Item Alpha", "Item Beta"],
        "total_amount": [50.0, 75.0, 100.0, 100.0, 120.0, 240.0],
    }
    df = pd.DataFrame(data)

    detector = DuplicateDetector()
    findings = detector.detect(df, primary_key="order_id", entity_key="customer_name")

    # Verify:
    # 1. Exact duplicate on row 3 (Bob Jones)
    # 2. Key conflict on ORD99 (conflicting line items / amounts)
    # 3. Alice Smith (rows 0 and 1) is a legitimate repeat customer and must NOT be flagged as a duplicate issue!

    issue_findings = [f for f in findings if f.metadata.get("status") != "not_an_issue"]
    flagged_indices = []
    for f in issue_findings:
        flagged_indices.extend(f.affected_row_indices)

    assert 0 not in flagged_indices, "Valid repeat order for Alice (row 0) should not be flagged"
    assert 1 not in flagged_indices, "Valid repeat order for Alice (row 1) should not be flagged"
    assert 3 in flagged_indices, "Exact duplicate for Bob (row 3) must be flagged"
    assert 4 in flagged_indices or 5 in flagged_indices, "Key conflict on ORD99 must be flagged"

def test_auto_detect_candidate_keys():
    data = {
        "txn_id": [f"TXN_{i}" for i in range(10)],
        "user_email": ["user1@test.com", "user1@test.com"] + [f"u{i}@test.com" for i in range(2, 10)],
        "date": ["2026-01-01"] * 10,
        "amount": [10.0] * 10,
    }
    df = pd.DataFrame(data)

    detector = DuplicateDetector()
    pk, ek = detector.infer_keys(df)

    assert pk == "txn_id", f"Expected primary key 'txn_id', got '{pk}'"
    assert ek == "user_email", f"Expected entity key 'user_email', got '{ek}'"
