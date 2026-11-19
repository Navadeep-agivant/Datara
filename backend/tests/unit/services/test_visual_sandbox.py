import uuid
import pandas as pd
import pytest
from app.models.finding import Finding
from app.services.cleaner import CleaningService

def test_visual_sandbox_diff_generation_and_partitioning():
    service = CleaningService()
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3"],
        "city": ["mumbai", "MUMBAI", "Delhi"],
        "quantity": [2, 1, 3],
        "unit_price": [500.0, 1000.0, 100.0],
        "total_amount": [1000.0, 1500.0, 300.0],  # Row 1 is 1 * 1000 != 1500
        "rating": [5.0, None, 4.0]
    })

    f_casing = Finding(
        finding_id=uuid.uuid4(),
        issue_family="inconsistent",
        affected_columns=["city"],
        affected_row_indices=[0, 1],
        severity="warning",
        detection_methods=["fuzzy"],
        metadata={"canonical_candidate": "Mumbai"}
    )
    f_arithmetic = Finding(
        finding_id=uuid.uuid4(),
        issue_family="arithmetic_conflict",
        affected_columns=["quantity", "unit_price", "total_amount"],
        affected_row_indices=[1],
        severity="error",
        detection_methods=["cross_column_arithmetic"],
        metadata={"formula": "quantity * unit_price == total_amount"}
    )
    f_missing_rating = Finding(
        finding_id=uuid.uuid4(),
        issue_family="missing",
        affected_columns=["rating"],
        affected_row_indices=[1],
        severity="warning",
        detection_methods=["null_check"]
    )

    operations = service.generate_proposed_operations([f_casing, f_arithmetic, f_missing_rating])
    assert len(operations) == 3

    # Generate sandbox diffs for each operation
    for op in operations:
        diffs = service.preview_operation(df, op, None)
        op.preview_diff = diffs

    # 1. Casing operation has diffs for row 0 and 1
    op_casing = next(o for o in operations if o.operation_type == "case_normalization")
    assert op_casing.bucket == "auto_fixable"
    assert len(op_casing.preview_diff) >= 1
    assert op_casing.preview_diff[0].column_name == "city"

    # 2. Arithmetic recalculation has diff for total_amount in row 1
    op_arithmetic = next(o for o in operations if o.operation_type == "recalculate_arithmetic")
    assert op_arithmetic.bucket == "auto_fixable"
    assert len(op_arithmetic.preview_diff) == 1
    assert op_arithmetic.preview_diff[0].before == "1500.0"
    assert float(op_arithmetic.preview_diff[0].after) == 1000.0

    # 3. Missing rating is classified as needs_review, preserving nulls
    op_rating = next(o for o in operations if "rating" in o.affected_columns)
    assert op_rating.bucket == "needs_review"
    assert len(op_rating.preview_diff) == 0  # Honest null preservation: no synthetic overwrite
