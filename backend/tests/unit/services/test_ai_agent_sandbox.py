import uuid
import pandas as pd
import pytest
from app.models.finding import Finding
from app.models.cleaning import CleaningOperation
from app.services.cleaner import CleaningService
from app.services.ai_agent import ai_remediation_agent

def test_ai_remediation_agent_contextual_synthesis():
    # 1. Email synthesis from customer_name
    res_email = ai_remediation_agent.suggest_remediation(
        row_index=0,
        column_name="email",
        current_value=None,
        context_row={"customer_name": "Bob Wilson", "city": "Bangalore"}
    )
    assert res_email["suggested_value"] == "bob.wilson@store.com"
    assert "Bob Wilson" in res_email["rationale"]

    # 2. Phone synthesis based on city context
    res_phone = ai_remediation_agent.suggest_remediation(
        row_index=1,
        column_name="phone",
        current_value="0000000000",
        context_row={"city": "Mumbai"}
    )
    assert "+91" in res_phone["suggested_value"]

    # 3. Calendar-impossible date correction
    res_date = ai_remediation_agent.suggest_remediation(
        row_index=2,
        column_name="order_date",
        current_value="2026-02-30",
        context_row={}
    )
    assert res_date["suggested_value"] == "2026-02-28"

    # 4. Out-of-bounds rating calibration
    res_rating = ai_remediation_agent.suggest_remediation(
        row_index=3,
        column_name="rating",
        current_value="10",
        context_row={}
    )
    assert float(res_rating["suggested_value"]) <= 5.0

    # 5. Arithmetic recalculation
    res_arith = ai_remediation_agent.suggest_remediation(
        row_index=4,
        column_name="total_amount",
        current_value="2500.0",
        context_row={"quantity": 2, "unit_price": 1000.0}
    )
    assert res_arith["suggested_value"] == "2000.0"

def test_regenerate_pandas_code_from_edited_diffs():
    service = CleaningService()
    op = CleaningOperation(
        operation_id=uuid.uuid4(),
        finding_id="find-1",
        operation_type="fill_missing",
        affected_columns=["email"],
        affected_row_indices=[0],
        bucket="needs_review",
        approval_status="pending"
    )
    df = pd.DataFrame({"email": [None]})
    diffs = service.preview_operation(df, op, None, include_unmutated=True)
    assert len(diffs) == 1
    diffs[0].after = "bob.wilson@store.com"
    op.preview_diff = diffs

    code = service.regenerate_pandas_code_from_diffs(op)
    assert "df.loc[0, 'email'] = 'bob.wilson@store.com'" in code
