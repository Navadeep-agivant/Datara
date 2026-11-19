from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.utils.session import session_store
from app.services.cleaner import cleaning_service
from app.services.scorer import calculate_quality_scores
from app.services.ai_agent import ai_remediation_agent
from app.models.cleaning import CellDiff

router = APIRouter(prefix="/sessions", tags=["Cleaning"])

class ApproveRequest(BaseModel):
    operation_ids: List[str]

class CellEdit(BaseModel):
    row_index: int
    column_name: str
    after: str

class SandboxEditRequest(BaseModel):
    operation_id: str
    edits: List[CellEdit]

class AISuggestRequest(BaseModel):
    operation_id: str
    row_index: Optional[int] = None
    column_name: Optional[str] = None

@router.get("/{session_id}/clean")
def get_cleaning_operations(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not state.cleaning_operations and state.findings:
        state.cleaning_operations = cleaning_service.generate_proposed_operations(state.findings)

    return {
        "session_id": session_id,
        "operations": [op.model_dump() for op in state.cleaning_operations]
    }

@router.get("/{session_id}/clean/preview")
def preview_operation(session_id: str, operation_id: str = Query(...)):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    op = next((o for o in state.cleaning_operations if str(o.operation_id) == operation_id), None)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")

    if op.preview_diff is None:
        finding = next((f for f in state.findings if str(f.finding_id) == op.finding_id), None)
        diffs = cleaning_service.preview_operation(state.working_df, op, finding, include_unmutated=True)
        op.preview_diff = diffs

    return {
        "operation_id": operation_id,
        "diff": [d.model_dump() for d in op.preview_diff],
        "pandas_code": op.pandas_code
    }

@router.post("/{session_id}/clean/sandbox-edit")
def edit_sandbox_operation(session_id: str, req: SandboxEditRequest):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    op = next((o for o in state.cleaning_operations if str(o.operation_id) == req.operation_id), None)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")

    finding = next((f for f in state.findings if str(f.finding_id) == op.finding_id), None)
    if op.preview_diff is None:
        op.preview_diff = cleaning_service.preview_operation(state.working_df, op, finding, include_unmutated=True)

    for edit in req.edits:
        existing = next((d for d in op.preview_diff if d.row_index == edit.row_index and d.column_name == edit.column_name), None)
        if existing:
            existing.after = edit.after
        else:
            before_val = str(state.working_df.at[edit.row_index, edit.column_name]) if edit.row_index in state.working_df.index else ""
            op.preview_diff.append(CellDiff(
                row_index=edit.row_index,
                column_name=edit.column_name,
                before=before_val,
                after=edit.after
            ))

    op.pandas_code = cleaning_service.regenerate_pandas_code_from_diffs(op)

    return {
        "operation_id": req.operation_id,
        "diff": [d.model_dump() for d in op.preview_diff],
        "pandas_code": op.pandas_code
    }

@router.post("/{session_id}/clean/ai-suggest")
def ai_suggest_remediation(session_id: str, req: AISuggestRequest):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    op = next((o for o in state.cleaning_operations if str(o.operation_id) == req.operation_id), None)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")

    finding = next((f for f in state.findings if str(f.finding_id) == op.finding_id), None)
    if op.preview_diff is None:
        op.preview_diff = cleaning_service.preview_operation(state.working_df, op, finding, include_unmutated=True)

    suggestions = []
    target_cells = []
    if req.row_index is not None and req.column_name is not None:
        target_cells.append((req.row_index, req.column_name))
    else:
        for d in op.preview_diff:
            target_cells.append((d.row_index, d.column_name))

    for r_idx, col in target_cells:
        if r_idx not in state.working_df.index or col not in state.working_df.columns:
            continue
        context_row = state.working_df.loc[r_idx].to_dict()
        cur_val = state.working_df.at[r_idx, col]
        sugg = ai_remediation_agent.suggest_remediation(
            row_index=r_idx,
            column_name=col,
            current_value=cur_val,
            context_row=context_row,
            finding=finding
        )
        suggestions.append({
            "row_index": r_idx,
            "column_name": col,
            "suggested_value": sugg["suggested_value"],
            "rationale": sugg["rationale"],
            "confidence": sugg["confidence"]
        })

        existing = next((d for d in op.preview_diff if d.row_index == r_idx and d.column_name == col), None)
        if existing:
            existing.after = sugg["suggested_value"]
        else:
            op.preview_diff.append(CellDiff(
                row_index=r_idx,
                column_name=col,
                before=str(cur_val),
                after=sugg["suggested_value"]
            ))

    op.pandas_code = cleaning_service.regenerate_pandas_code_from_diffs(op)

    return {
        "operation_id": req.operation_id,
        "suggestions": suggestions,
        "diff": [d.model_dump() for d in op.preview_diff],
        "pandas_code": op.pandas_code
    }

@router.post("/{session_id}/clean/approve")
def approve_operations(session_id: str, req: ApproveRequest):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    applied_ids = []
    for op_id_str in req.operation_ids:
        op = next((o for o in state.cleaning_operations if str(o.operation_id) == op_id_str), None)
        if op and op.approval_status != "approved":
            finding = next((f for f in state.findings if str(f.finding_id) == op.finding_id), None)
            diffs = op.preview_diff or cleaning_service.preview_operation(state.working_df, op, finding)
            state.working_df, _ = cleaning_service.apply_operation(state.working_df, op, diffs)
            state.applied_cleaning_history.append(op)
            applied_ids.append(op_id_str)
            if finding:
                finding.is_resolved = True

    # Recompute quality score after cleaning
    updated_score = calculate_quality_scores(state.working_df, state.findings)
    state.quality_score_after = updated_score

    return {
        "applied_operations": applied_ids,
        "quality_score_after": updated_score.model_dump()
    }

@router.post("/{session_id}/clean/apply-all-low-risk")
def apply_all_low_risk(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not state.cleaning_operations and state.findings:
        state.cleaning_operations = cleaning_service.generate_proposed_operations(state.findings)

    findings_map = {str(f.finding_id): f for f in state.findings}
    state.working_df, applied_ops = cleaning_service.apply_all_low_risk(
        state.working_df, state.cleaning_operations, findings_map
    )

    applied_ids = []
    for op in applied_ops:
        state.applied_cleaning_history.append(op)
        applied_ids.append(str(op.operation_id))
        finding = findings_map.get(op.finding_id)
        if finding:
            finding.is_resolved = True

    updated_score = calculate_quality_scores(state.working_df, state.findings)
    state.quality_score_after = updated_score

    return {
        "applied_operations": applied_ids,
        "quality_score_after": updated_score.model_dump()
    }

@router.post("/{session_id}/clean/undo")
def undo_last_operation(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not state.applied_cleaning_history:
        raise HTTPException(status_code=409, detail="Nothing to undo.")

    last_op = state.applied_cleaning_history.pop()
    state.working_df = cleaning_service.undo_operation(state.working_df, last_op)

    # Unresolve finding
    finding = next((f for f in state.findings if str(f.finding_id) == last_op.finding_id), None)
    if finding:
        finding.is_resolved = False

    updated_score = calculate_quality_scores(state.working_df, state.findings)
    state.quality_score_after = updated_score

    return {
        "undone_operation_id": str(last_op.operation_id),
        "quality_score_after": updated_score.model_dump()
    }
