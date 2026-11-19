from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.session import session_store
from app.detectors.missing import MissingValueDetector
from app.detectors.duplicates import DuplicateDetector
from app.detectors.outliers import OutlierDetector
from app.detectors.inconsistent import InconsistentValueDetector
from app.detectors.validation import ArithmeticValidationDetector
from app.detectors.validity import ValidityDetector
from app.detectors.registry import detector_registry
from app.services.scorer import calculate_quality_scores

router = APIRouter(prefix="/sessions", tags=["Detection"])

class DetectRequest(BaseModel):
    primary_key: Optional[str] = None
    entity_key: Optional[str] = None
    arithmetic_tolerance: Optional[float] = 0.01
    outlier_iqr_multiplier: Optional[float] = 1.5
    fuzzy_threshold: Optional[int] = 85

@router.post("/{session_id}/detect")
def run_detection(session_id: str, req: DetectRequest = DetectRequest()):
    state = session_store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    df = state.working_df

    # Run detectors
    missing_det = MissingValueDetector()
    dupes_det = DuplicateDetector()
    outlier_det = OutlierDetector(iqr_multiplier=req.outlier_iqr_multiplier or 1.5)
    inconsistent_det = InconsistentValueDetector(threshold=req.fuzzy_threshold or 85)
    arithmetic_det = ArithmeticValidationDetector(tolerance=req.arithmetic_tolerance or 0.01)
    validity_det = ValidityDetector()

    # Key inference for relational deduplication
    inferred_pk, inferred_ek = dupes_det.infer_keys(df)
    active_pk = req.primary_key or inferred_pk
    active_ek = req.entity_key or inferred_ek

    all_findings = []
    all_findings.extend(missing_det.detect(df))
    all_findings.extend(dupes_det.detect(df, primary_key=active_pk, entity_key=active_ek))
    all_findings.extend(outlier_det.detect(df))
    all_findings.extend(inconsistent_det.detect(df))
    all_findings.extend(arithmetic_det.detect(df, tolerance=req.arithmetic_tolerance or 0.01))
    all_findings.extend(validity_det.detect(df))

    # Run dynamically learned custom rules from registry for continuous learning
    for rule in detector_registry.get_custom_rules():
        if rule.get("is_active", True):
            all_findings.extend(detector_registry.run_custom_rule(df, rule))

    state.findings = all_findings

    # Calculate score
    quality_score = calculate_quality_scores(df, all_findings)
    state.quality_score_before = quality_score

    return {
        "session_id": session_id,
        "primary_key": active_pk,
        "entity_key": active_ek,
        "total_findings": len(all_findings),
        "findings": [f.model_dump() for f in all_findings],
        "quality_score": quality_score.model_dump()
    }
