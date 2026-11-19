import tempfile
import os
import pandas as pd
import pytest
from app.services.synthesizer import AdaptiveRuleSynthesizer
from app.detectors.registry import DetectorRegistry

def test_adaptive_synthesizer_discovers_and_validates_novel_rule():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        registry = DetectorRegistry(storage_path=temp_path)
        synthesizer = AdaptiveRuleSynthesizer(registry=registry)

        # Dataset with a novel unscripted corrupt sentinel: "CORRUPT_VALUE_999"
        df = pd.DataFrame({
            "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
            "status": ["Completed", "Pending", "CORRUPT_VALUE_999", "Completed"],
            "amount": [100.0, 200.0, 300.0, 400.0]
        })

        # 1. Discover novel patterns
        synthesized_rules = synthesizer.analyze_and_synthesize(df)
        assert len(synthesized_rules) >= 1

        rule = synthesized_rules[0]
        assert "status" in rule["target_columns"]
        assert rule["rule_id"].startswith("rule_")
        assert "remediation_code" in rule

        # 2. Verify safety check (assert zero false positives on clean rows 0, 1, 3)
        clean_df = df.loc[[0, 1, 3]]
        is_safe = synthesizer.verify_rule_safety(rule, clean_df)
        assert is_safe is True

        # 3. Register the rule into the registry
        registry.register_rule(rule)
        assert len(registry.get_custom_rules()) == 1

        # 4. Verify detection on full dataset flags row 2
        findings = registry.run_all(df)
        novel_findings = [f for f in findings if f.metadata.get("rule_id") == rule["rule_id"]]
        assert len(novel_findings) == 1
        assert 2 in novel_findings[0].affected_row_indices
        assert 0 not in novel_findings[0].affected_row_indices
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
