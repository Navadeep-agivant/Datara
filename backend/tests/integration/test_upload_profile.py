import pandas as pd
from app.utils.session import session_store
from app.routers.profile import get_dataset_profile

def test_upload_and_profile_flow():
    session_id = "test-session-upload-profile"
    df = pd.DataFrame({"order_id": ["ORD1", "ORD2"], "price": [100, 200], "city": ["Mumbai", "Delhi"]})
    session_store.create_session(session_id, df, "test.csv", "utf-8", [])

    profile_res = get_dataset_profile(session_id)
    assert len(profile_res["profiles"]) == 3
