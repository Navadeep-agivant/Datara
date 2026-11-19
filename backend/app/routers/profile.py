from fastapi import APIRouter, HTTPException
from app.utils.session import session_store
from app.services.profiler import profile_dataframe

router = APIRouter(prefix="/sessions", tags=["Profile"])

@router.get("/{session_id}/profile")
def get_dataset_profile(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not state.column_profiles:
        # Profile on working copy
        state.column_profiles = profile_dataframe(state.working_df)

    return {
        "session_id": session_id,
        "profiles": [p.model_dump() for p in state.column_profiles]
    }
