import os
import json
import tempfile
import pandas as pd
import pytest
from app.detectors.registry import DetectorRegistry
from app.detectors.base import BaseDetector
from app.models.finding import Finding

def test_detector_registry_builtins_and_custom_rule_persistence():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        registry = DetectorRegistry(storage_path=temp_path)
        # 1. Built-in detectors should be loaded
        builtins = registry.get_builtin_detectors()
        assert len(builtins) >= 6

        # 2. Add a dynamic synthesized rule
        custom_rule = {
            "rule_id": "rule_test_postal_code",
            "rule_name": "Invalid Postal Code Detector",
            "target_columns": ["postal_code"],
            "pattern": r"^\d{5,6}$",  # Must be 5 or 6 digits
            "pattern_type": "regex_match",
            "severity": "warning",
            "description": "Flags postal codes that do not match standard 5 or 6 digit format."
        }
        registry.register_rule(custom_rule)

        # 3. Verify rule is active and persisted
        active_rules = registry.get_custom_rules()
        assert len(active_rules) == 1
        assert active_rules[0]["rule_id"] == "rule_test_postal_code"

        # 4. Create new registry instance pointing to same file and assert persistence
        new_registry = DetectorRegistry(storage_path=temp_path)
        assert len(new_registry.get_custom_rules()) == 1
        assert new_registry.get_custom_rules()[0]["rule_name"] == "Invalid Postal Code Detector"

        # 5. Run detection through registry with custom rule
        df = pd.DataFrame({
            "postal_code": ["12345", "ABCDE", "987654"]
        })
        findings = new_registry.run_all(df)
        custom_findings = [f for f in findings if f.metadata.get("rule_id") == "rule_test_postal_code"]
        assert len(custom_findings) == 1
        # "ABCDE" should be flagged as invalid
        assert 1 in custom_findings[0].affected_row_indices
        assert 0 not in custom_findings[0].affected_row_indices
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
