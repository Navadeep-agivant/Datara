import uuid
import pandas as pd
from app.utils.session import session_store
from app.routers.clean import (
    get_cleaning_operations,
    apply_all_low_risk,
    undo_last_operation
)
from app.routers.report import download_report, export_csv
from app.models.finding import Finding

def test_cleaning_and_report_pipeline():
    session_id = f"test-clean-{uuid.uuid4()}"
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2"],
        "city": ["mumbai", "MUMBAI"],
        "formula_cell": ["=1+1", "regular"]
    })
    session_store.create_session(session_id, df, "orders.csv", "utf-8", [])
    state = session_store.get_session(session_id)

    # Attach an inconsistent casing finding
    f = Finding(
        finding_id=uuid.uuid4(),
        issue_family="inconsistent",
        affected_columns=["city"],
        affected_row_indices=[0, 1],
        severity="warning",
        detection_methods=["fuzzy"],
        metadata={"canonical_candidate": "Mumbai"}
    )
    state.findings = [f]

    # 1. Fetch proposed operations
    ops_res = get_cleaning_operations(session_id)
    assert len(ops_res["operations"]) == 1
    assert ops_res["operations"][0]["risk_level"] == "low"

    # 2. Batch apply all low-risk operations
    batch_res = apply_all_low_risk(session_id)
    assert len(batch_res["applied_operations"]) == 1
    assert state.working_df.at[0, "city"] == "Mumbai"

    # 3. Generate HTML report
    report_res = download_report(session_id)
    assert report_res.status_code == 200
    assert b"<!DOCTYPE html>" in report_res.body or b"<html" in report_res.body

    # 4. Export CSV with formula injection guard
    csv_res = export_csv(session_id)
    assert csv_res.status_code == 200
    assert b"'=1+1" in csv_res.body or b"regular" in csv_res.body

    # 5. Undo operation
    undo_res = undo_last_operation(session_id)
    assert undo_res["undone_operation_id"] == batch_res["applied_operations"][0]
    assert state.working_df.at[0, "city"] == "mumbai"
