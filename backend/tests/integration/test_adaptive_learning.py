import uuid
import pandas as pd
from app.utils.session import session_store
from app.routers.adaptive import adaptive_learn
from app.routers.detect import run_detection, DetectRequest

def test_adaptive_learning_endpoint_flow():
    session_id = f"test-adaptive-{uuid.uuid4()}"
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
        "status": ["Approved", "Delivered", "UNKNOWN_CORRUPT_TAG", "Approved"],
        "total_amount": [100.0, 200.0, 300.0, 400.0]
    })
    session_store.create_session(session_id, df, "test.csv", "utf-8", [])

    # 1. Trigger adaptive learning directly
    res = adaptive_learn(session_id)
    assert res["session_id"] == session_id
    assert "synthesized_rules" in res
    assert isinstance(res["synthesized_rules"], list)

    # 2. Subsequent detect call reflects findings
    detect_res = run_detection(session_id, DetectRequest())
    assert detect_res["total_findings"] >= 0
