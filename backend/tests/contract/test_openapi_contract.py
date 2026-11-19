from app.main import app

def test_openapi_contract_schema():
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "AI Data Quality & Anomaly Detection Agent API"
    assert "/health" in schema["paths"]
    assert "/upload" in schema["paths"]
    assert "/sessions/{session_id}/profile" in schema["paths"]
    assert "/sessions/{session_id}/detect" in schema["paths"]
    assert "/sessions/{session_id}/score" in schema["paths"]
    assert "/sessions/{session_id}/explain" in schema["paths"]
    assert "/sessions/{session_id}/clean" in schema["paths"]
    assert "/sessions/{session_id}/clean/apply-all-low-risk" in schema["paths"]
    assert "/sessions/{session_id}/report" in schema["paths"]

