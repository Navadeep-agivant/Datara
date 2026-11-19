import os
import pandas as pd
import pytest
from app.detectors.missing import MissingValueDetector
from app.detectors.duplicates import DuplicateDetector
from app.detectors.outliers import OutlierDetector
from app.detectors.inconsistent import InconsistentValueDetector
from app.detectors.validation import ArithmeticValidationDetector
from app.detectors.validity import ValidityDetector
from app.services.scorer import calculate_quality_scores

def test_ground_truth_planted_anomalies_benchmark():
    # Find datasets/online_store_orders_sample.csv from repo root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = current_dir
    while repo_root and not os.path.exists(os.path.join(repo_root, "datasets", "online_store_orders_sample.csv")):
        parent = os.path.dirname(repo_root)
        if parent == repo_root:
            break
        repo_root = parent

    csv_path = os.path.join(repo_root, "datasets", "online_store_orders_sample.csv")
    assert os.path.exists(csv_path), f"Sample CSV not found at {csv_path}"
    df = pd.read_csv(csv_path)

    missing_det = MissingValueDetector()
    dupes_det = DuplicateDetector()
    outlier_det = OutlierDetector(iqr_multiplier=1.5)
    inconsistent_det = InconsistentValueDetector(threshold=85)
    arithmetic_det = ArithmeticValidationDetector(tolerance=0.01)
    validity_det = ValidityDetector()

    all_findings = []
    all_findings.extend(missing_det.detect(df))
    all_findings.extend(dupes_det.detect(df, primary_key="order_id", entity_key="customer_name"))
    all_findings.extend(outlier_det.detect(df))
    all_findings.extend(inconsistent_det.detect(df))
    all_findings.extend(arithmetic_det.detect(df, tolerance=0.01))
    all_findings.extend(validity_det.detect(df))

    # Verification checklist of planted anomalies (N of N detected):
    
    # 1. Impossible date (2026-02-30 in row index 7)
    date_findings = [f for f in all_findings if "order_date" in f.affected_columns and f.issue_family == "invalid"]
    assert len(date_findings) > 0
    assert 7 in date_findings[0].affected_row_indices

    # 2. Dummy phone (0000000000 in row index 2)
    phone_invalid = [f for f in all_findings if "phone" in f.affected_columns and f.issue_family == "invalid"]
    assert len(phone_invalid) > 0
    assert 2 in phone_invalid[0].affected_row_indices

    # 3. Missing phone (row index 12)
    phone_missing = [f for f in all_findings if "phone" in f.affected_columns and f.issue_family == "missing"]
    assert len(phone_missing) > 0
    assert 12 in phone_missing[0].affected_row_indices

    # 4. Invalid email syntax (bob.wilson@invalid-email in row index 2)
    email_invalid = [f for f in all_findings if "email" in f.affected_columns and f.issue_family == "invalid"]
    assert len(email_invalid) > 0
    assert 2 in email_invalid[0].affected_row_indices

    # 5. Missing email (row index 3)
    email_missing = [f for f in all_findings if "email" in f.affected_columns and f.issue_family == "missing"]
    assert len(email_missing) > 0
    assert 3 in email_missing[0].affected_row_indices

    # 6. Rating invalid (<1 or >5: 0 in row 2, 6 in row 5, 10 in row 10)
    rating_invalid = [f for f in all_findings if "rating" in f.affected_columns and f.issue_family == "invalid"]
    assert len(rating_invalid) > 0
    assert 2 in rating_invalid[0].affected_row_indices
    assert 5 in rating_invalid[0].affected_row_indices
    assert 10 in rating_invalid[0].affected_row_indices

    # 7. Missing rating (row index 4)
    rating_missing = [f for f in all_findings if "rating" in f.affected_columns and f.issue_family == "missing"]
    assert len(rating_missing) > 0
    assert 4 in rating_missing[0].affected_row_indices

    # 8. Negative delivery days (-3 in row index 6)
    delivery_invalid = [f for f in all_findings if "delivery_days" in f.affected_columns and f.issue_family == "invalid"]
    assert len(delivery_invalid) > 0
    assert 6 in delivery_invalid[0].affected_row_indices

    # 9. Non-positive quantity (-2 in row index 2)
    qty_invalid = [f for f in all_findings if "quantity" in f.affected_columns and f.issue_family == "invalid"]
    assert len(qty_invalid) > 0
    assert 2 in qty_invalid[0].affected_row_indices

    # 10. Outliers (Dave Miller quantity 120, total 54000 in row index 5)
    outlier_findings = [f for f in all_findings if f.issue_family == "outlier"]
    assert len(outlier_findings) > 0
    outlier_rows = [idx for f in outlier_findings for idx in f.affected_row_indices]
    assert 5 in outlier_rows

    # 11. Cross-column arithmetic mismatch (2 * 1000 != 2500 in row index 8)
    arithmetic_findings = [f for f in all_findings if f.issue_family == "arithmetic_conflict"]
    assert len(arithmetic_findings) > 0
    assert 8 in arithmetic_findings[0].affected_row_indices

    # 12. Exact duplicate (row index 9 is identical to row index 0) -> Tier A
    exact_dupes = [f for f in all_findings if f.metadata.get("tier") == "tier_a" or f.metadata.get("classification") == "exact_duplicate"]
    assert len(exact_dupes) > 0
    assert 0 in exact_dupes[0].affected_row_indices
    assert 9 in exact_dupes[0].affected_row_indices

    # 13. ID Collision (row index 13 and 16 share ORD-1014 with different payloads) -> Tier B
    key_collisions = [f for f in all_findings if f.metadata.get("tier") == "tier_b" or f.metadata.get("classification") == "id_collision"]
    assert len(key_collisions) > 0
    assert 13 in key_collisions[0].affected_row_indices
    assert 16 in key_collisions[0].affected_row_indices

    # 14. Repeat customer (Jane Smith in row index 1 and 15) -> Tier C ("Not an issue")
    repeat_customers = [f for f in all_findings if f.metadata.get("tier") == "tier_c" or f.metadata.get("classification") == "repeat_customer"]
    assert len(repeat_customers) > 0
    assert repeat_customers[0].metadata.get("status") == "not_an_issue"

    # 15. Inconsistent city & category & payment
    inconsistent_findings = [f for f in all_findings if f.issue_family == "inconsistent"]
    assert len(inconsistent_findings) > 0

    # Ensure scoring incorporates calibrated weights
    score = calculate_quality_scores(df, all_findings)
    assert score.overall_score < 100.0
