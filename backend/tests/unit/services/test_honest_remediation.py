import pandas as pd
import pytest
import uuid
from app.services.cleaner import CleaningService
from app.models.finding import Finding
from app.models.cleaning import CleaningOperation

def test_exact_arithmetic_recalculation():
    service = CleaningService()
    df = pd.DataFrame({
        "order_id": ["ORD-1009"],
        "quantity": [2],
        "unit_price": [1000.0],
        "total_amount": [2500.0]  # Should be 2000.0
    })
    finding = Finding(
        finding_id=uuid.uuid4(),
        issue_family="arithmetic_conflict",
        affected_columns=["quantity", "unit_price", "total_amount"],
        affected_row_indices=[0],
        severity="error",
        detection_methods=["cross_column_arithmetic"],
        metadata={"formula": "quantity * unit_price == total_amount"}
    )
    op = CleaningOperation(
        operation_id=uuid.uuid4(),
        finding_id=str(finding.finding_id),
        operation_type="recalculate_arithmetic",
        risk_level="low",
        affected_columns=["total_amount"],
        affected_row_indices=[0],
        bucket="auto_fixable"
    )

    diffs = service.preview_operation(df, op, finding)
    assert len(diffs) == 1
    assert diffs[0].column_name == "total_amount"
    assert diffs[0].before == "2500.0"
    assert float(diffs[0].after) == 2000.0  # Exact calculation, NOT median!

    df_cleaned, _ = service.apply_operation(df, op, diffs)
    assert float(df_cleaned.at[0, "total_amount"]) == 2000.0

def test_honest_null_preservation_for_rating_email_phone():
    service = CleaningService()
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3"],
        "rating": [5.0, None, 4.0],
        "email": ["user@test.com", None, "alice@test.com"],
        "phone": ["9876543210", None, "9876543211"]
    })
    findings = [
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="missing",
            affected_columns=["rating"],
            affected_row_indices=[1],
            severity="warning",
            detection_methods=["null_check"]
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="missing",
            affected_columns=["email"],
            affected_row_indices=[1],
            severity="warning",
            detection_methods=["null_check"]
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="missing",
            affected_columns=["phone"],
            affected_row_indices=[1],
            severity="warning",
            detection_methods=["null_check"]
        )
    ]
    ops = service.generate_proposed_operations(findings)
    for op in ops:
        # Operations for rating, email, phone should be classified as "needs_review", preserving nulls
        assert op.bucket == "needs_review"
        diffs = service.preview_operation(df, op, None)
        # Should NOT fabricate fake values like "Not Provided" or synthetic median for honest data quality
        for diff in diffs:
            assert diff.after != "Not Provided"

def test_partition_operations_auto_fixable_vs_needs_review():
    service = CleaningService()
    findings = [
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="duplicate",
            affected_columns=["order_id"],
            affected_row_indices=[0, 1],
            severity="warning",
            detection_methods=["exact_hash"],
            metadata={"tier": "tier_a", "classification": "exact_duplicate", "action": "auto_drop"}
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="duplicate",
            affected_columns=["order_id"],
            affected_row_indices=[2, 3],
            severity="error",
            detection_methods=["business_key_conflict"],
            metadata={"tier": "tier_b", "classification": "id_collision", "action": "manual_review"}
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="outlier",
            affected_columns=["total_amount"],
            affected_row_indices=[4],
            severity="warning",
            detection_methods=["iqr"]
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="inconsistent",
            affected_columns=["city"],
            affected_row_indices=[5],
            severity="warning",
            detection_methods=["fuzzy"],
            metadata={"canonical_candidate": "Mumbai"}
        )
    ]
    ops = service.generate_proposed_operations(findings)
    auto_fixable = [op for op in ops if op.bucket == "auto_fixable"]
    needs_review = [op for op in ops if op.bucket == "needs_review"]

    # Exact duplicate and inconsistent text are auto_fixable
    auto_fixable_types = [op.operation_type for op in auto_fixable]
    assert "drop_exact_duplicate" in auto_fixable_types or "case_normalization" in auto_fixable_types

    # ID Collision and Outliers are strictly needs_review
    assert any(op.finding_id == str(findings[1].finding_id) for op in needs_review)
    assert any(op.finding_id == str(findings[2].finding_id) for op in needs_review)
