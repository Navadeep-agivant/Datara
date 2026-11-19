import pytest
import uuid
from app.models.finding import Finding
from app.services.explainer import generate_deterministic_fallback, ExplainerService

def test_deterministic_fallback():
    f = Finding(
        finding_id=uuid.uuid4(),
        issue_family="missing",
        affected_columns=["city"],
        affected_row_indices=[1, 2],
        severity="error",
        detection_methods=["token_scan"],
        example_rows=[]
    )
    expl = generate_deterministic_fallback(f)
    assert expl.finding_id == str(f.finding_id)
    assert not expl.is_ai_generated
    assert "city" in expl.explanation_text
    assert expl.operation_hint in ("fill_missing", "review_only")
    assert expl.requires_approval is True
