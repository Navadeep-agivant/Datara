from fastapi import APIRouter, HTTPException, Response
from app.utils.session import session_store
from app.services.reporter import render_html_report, export_cleaned_csv

router = APIRouter(prefix="/sessions", tags=["Reports"])

@router.get("/{session_id}/report")
def download_report(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    html_content = render_html_report(state)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=quality_report_{state.filename}.html"}
    )

@router.get("/{session_id}/export/csv")
def export_csv(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    csv_bytes = export_cleaned_csv(state)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cleaned_{state.filename}"}
    )
