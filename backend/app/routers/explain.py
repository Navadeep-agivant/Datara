from fastapi import APIRouter, HTTPException
from app.utils.session import session_store
from app.services.explainer import explainer_service

router = APIRouter(prefix="/sessions", tags=["Explanation"])

@router.get("/{session_id}/explain")
async def get_findings_explanations(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not state.explanations and state.findings:
        state.explanations = await explainer_service.explain_findings(state.findings)

    return {
        "session_id": session_id,
        "explanations": {k: v.model_dump() for k, v in state.explanations.items()}
    }
