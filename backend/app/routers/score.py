from fastapi import APIRouter, HTTPException
from app.utils.session import session_store

router = APIRouter(prefix="/sessions", tags=["Score"])

@router.get("/{session_id}/score")
def get_session_score(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return {
        "score_before": state.quality_score_before.model_dump() if state.quality_score_before else None,
        "score_after": state.quality_score_after.model_dump() if state.quality_score_after else None
    }
