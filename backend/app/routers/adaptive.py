from fastapi import APIRouter, HTTPException
from app.utils.session import session_store
from app.services.synthesizer import adaptive_synthesizer
from app.detectors.registry import detector_registry
from app.services.scorer import calculate_quality_scores

router = APIRouter(prefix="/sessions", tags=["Adaptive Learning"])

@router.post("/{session_id}/adaptive-learn")
def adaptive_learn(session_id: str):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    df = state.working_df

    # 1. Discover novel patterns and synthesize candidate rules
    synthesized_rules = adaptive_synthesizer.analyze_and_synthesize(df)

    registered_rules = []
    new_findings = []

    for rule in synthesized_rules:
        # 2. Register rule in persistent registry
        detector_registry.register_rule(rule)
        registered_rules.append(rule)
        # 3. Execute rule against current dataframe
        findings = detector_registry.run_custom_rule(df, rule)
        new_findings.extend(findings)

    # Attach new findings to session state if any
    if new_findings:
        state.findings.extend(new_findings)
        state.quality_score_before = calculate_quality_scores(df, state.findings)

    return {
        "session_id": session_id,
        "synthesized_rules": registered_rules,
        "new_findings_count": len(new_findings),
        "message": f"Synthesized and registered {len(registered_rules)} novel anomaly detection rule(s)."
    }
