import uuid
import pandas as pd
import pytest
from app.models.finding import Finding
from app.services.cleaner import CleaningService

def test_always_generate_executable_pandas_code():
    service = CleaningService()
    findings = [
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="inconsistent",
            affected_columns=["city"],
            affected_row_indices=[0, 1],
            severity="warning",
            detection_methods=["fuzzy"],
            metadata={"canonical_candidate": "Mumbai"}
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="arithmetic_conflict",
            affected_columns=["quantity", "unit_price", "total_amount"],
            affected_row_indices=[2],
            severity="error",
            detection_methods=["cross_column_arithmetic"],
            metadata={"formula": "quantity * unit_price == total_amount"}
        ),
        Finding(
            finding_id=uuid.uuid4(),
            issue_family="duplicate",
            affected_columns=["order_id"],
            affected_row_indices=[3, 4],
            severity="warning",
            detection_methods=["exact_hash"],
            metadata={"tier": "tier_a", "classification": "exact_duplicate", "action": "auto_drop"}
        )
    ]

    operations = service.generate_proposed_operations(findings)
    assert len(operations) == 3

    for op in operations:
        # Every proposed operation MUST provide executable pandas code per Principle XII
        assert op.pandas_code is not None, f"Operation {op.operation_type} is missing pandas_code"
        assert len(op.pandas_code.strip()) > 0
        # Assert syntactically valid Python code
        compile(op.pandas_code, "<string>", "exec")

    # Specific code checks
    op_casing = next(o for o in operations if o.operation_type == "case_normalization")
    assert "city" in op_casing.pandas_code
    assert "Mumbai" in op_casing.pandas_code or "title" in op_casing.pandas_code

    op_arithmetic = next(o for o in operations if o.operation_type == "recalculate_arithmetic")
    assert "total_amount" in op_arithmetic.pandas_code
    assert "*" in op_arithmetic.pandas_code

    op_duplicate = next(o for o in operations if o.operation_type == "drop_exact_duplicate")
    assert "drop_duplicates" in op_duplicate.pandas_code
