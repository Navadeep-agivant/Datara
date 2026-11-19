import uuid
import pandas as pd
from app.models.finding import Finding
from app.services.cleaner import CleaningService

def test_risk_classification_and_apply_all_low_risk():
    service = CleaningService()

    f_inconsistent = Finding(
        finding_id=uuid.uuid4(),
        issue_family="inconsistent",
        affected_columns=["city"],
        affected_row_indices=[0, 1],
        severity="warning",
        detection_methods=["fuzzy"],
        metadata={"canonical_candidate": "Mumbai"}
    )

    f_missing = Finding(
        finding_id=uuid.uuid4(),
        issue_family="missing",
        affected_columns=["notes"],
        affected_row_indices=[2],
        severity="info",
        detection_methods=["null_check"]
    )

    operations = service.generate_proposed_operations([f_inconsistent, f_missing])
    assert len(operations) == 2

    # Check risk levels
    op_casing = next(op for op in operations if op.operation_type == "case_normalization")
    op_missing = next(op for op in operations if op.operation_type == "fill_missing")

    assert op_casing.risk_level == "low"
    assert op_missing.risk_level == "medium"

    # Test applying all low-risk operations
    df = pd.DataFrame({
        "city": ["mumbai", "MUMBAI", "Delhi"],
        "notes": ["ok", "ok", None]
    })

    findings_map = {str(f.finding_id): f for f in [f_inconsistent, f_missing]}
    updated_df, applied_ops = service.apply_all_low_risk(df, operations, findings_map)

    # Low risk operation should be applied
    assert len(applied_ops) == 1
    assert applied_ops[0].operation_id == op_casing.operation_id
    assert applied_ops[0].approval_status == "approved"
    assert updated_df.at[0, "city"] == "Mumbai"
    assert updated_df.at[1, "city"] == "Mumbai"

    # Medium risk operation should remain pending
    assert op_missing.approval_status == "pending"
    assert pd.isna(updated_df.at[2, "notes"])
