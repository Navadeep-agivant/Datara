import uuid
import re
from app.models.finding import Finding
from app.services.explainer import ExplainerService

def test_explainer_fallback_includes_mcp_action_and_polyglot_regex():
    service = ExplainerService()

    # Finding 1: Inconsistent city/phone strings
    finding = Finding(
        finding_id=uuid.uuid4(),
        issue_family="inconsistent",
        affected_columns=["phone_number"],
        affected_row_indices=[1, 4, 7],
        severity="warning",
        detection_methods=["format_inconsistency"],
        example_rows=[{"phone_number": "+91-98765-43210"}, {"phone_number": "9876543210"}],
        metadata={"match_type": "format_variant"}
    )

    explanation = service.explain_finding(finding)

    assert explanation.finding_id == str(finding.finding_id)
    assert not explanation.is_ai_generated  # fallback active

    # Verify MCP Action Blueprint
    mcp = explanation.mcp_action
    assert mcp is not None
    assert mcp.tool_name != ""
    assert mcp.risk_level in ["low", "medium", "high"]
    assert "tool_name" in mcp.rollback_action or "parameters" in mcp.rollback_action

    # Verify Polyglot Regex for phone
    poly = explanation.polyglot_regex
    assert poly is not None
    assert poly.domain in ["phone", "postal_code", "date", "general"]
    assert len(poly.target_locales) > 0
    # Pattern should compile
    compiled = re.compile(poly.regex_pattern)
    assert compiled is not None

def test_explainer_fallback_for_arithmetic_conflict():
    service = ExplainerService()

    finding = Finding(
        finding_id=uuid.uuid4(),
        issue_family="arithmetic_conflict",
        affected_columns=["quantity", "unit_price", "total_amount"],
        affected_row_indices=[2, 5],
        severity="error",
        detection_methods=["cross_column_arithmetic"],
        example_rows=[{"quantity": 10, "unit_price": 5.0, "total_amount": 75.0}],
        metadata={"formula": "quantity * unit_price == total_amount", "tolerance": 0.01}
    )

    explanation = service.explain_finding(finding)
    assert explanation.mcp_action is not None
    assert explanation.mcp_action.tool_name in ["recalculate_column", "flag_for_review", "fix_arithmetic"]
    assert explanation.mcp_action.risk_level in ["medium", "high"]
