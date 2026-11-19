import pandas as pd
from app.utils.session import session_store
from app.routers.detect import run_detection, DetectRequest
from app.routers.score import get_session_score

def test_detection_and_score_pipeline():
    session_id = "test-session-pipeline"
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-1", "ORD-4"],
        "quantity": [2, 1, -2, 2, None],
        "unit_price": [500.0, 1200.0, 300.0, 500.0, 100.0],
        "city": ["Mumbai", "mumbai", "Bangalore", "Mumbai", "Delhi"]
    })
    session_store.create_session(session_id, df, "test.csv", "utf-8", [])

    det_res = run_detection(session_id, DetectRequest())
    assert det_res["total_findings"] > 0
    assert det_res["quality_score"]["overall_score"] <= 100.0

    score_res = get_session_score(session_id)
    assert score_res["score_before"] is not None
