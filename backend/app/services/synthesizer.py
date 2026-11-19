import re
import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
from app.detectors.registry import DetectorRegistry, detector_registry

class AdaptiveRuleSynthesizer:
    def __init__(self, registry: Optional[DetectorRegistry] = None):
        self.registry = registry or detector_registry
        self.novel_suspicious_patterns = [
            re.compile(r"(?i).*(corrupt|unknown_corrupt|err_|###|bad_val|faulty|invalid_token|broken|#null#).*"),
            re.compile(r"^[A-Z0-9_]{12,}$"),  # Extreme all-caps technical codes leaking into text
        ]

    def analyze_and_synthesize(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        synthesized_rules: List[Dict[str, Any]] = []
        if len(df) == 0:
            return synthesized_rules

        for col in df.columns:
            if not pd.api.types.is_object_dtype(df[col]) and not pd.api.types.is_string_dtype(df[col]):
                continue

            # Inspect distinct non-null values
            non_null_vals = df[col].dropna().astype(str).str.strip()
            if non_null_vals.empty:
                continue

            detected_pattern_strings = set()
            for val in non_null_vals:
                for pattern in self.novel_suspicious_patterns:
                    if pattern.search(val):
                        # Clean regex escape for the detected token or keyword
                        matched_token = val.replace("\\", "\\\\")
                        detected_pattern_strings.add(re.escape(val))

            if detected_pattern_strings:
                combined_regex = "|".join(sorted(list(detected_pattern_strings)))
                rule_id = f"rule_{uuid.uuid4().hex[:8]}"
                remediation_code = f"# Remediate novel anomaly in '{col}'\ndf.loc[df['{col}'].astype(str).str.contains(r'{combined_regex}', na=False), '{col}'] = None"

                rule = {
                    "rule_id": rule_id,
                    "rule_name": f"Adaptive Detector for {col}",
                    "target_columns": [col],
                    "pattern": combined_regex,
                    "pattern_type": "anomaly_regex",
                    "severity": "warning",
                    "description": f"Dynamically synthesized rule flagging novel corrupt tokens in '{col}'.",
                    "remediation_code": remediation_code,
                    "is_active": True
                }
                synthesized_rules.append(rule)

        return synthesized_rules

    def verify_rule_safety(self, rule: Dict[str, Any], clean_df: pd.DataFrame) -> bool:
        """
        Safety check: Asserts that a newly synthesized rule produces ZERO false positives on clean rows.
        """
        findings = self.registry.run_custom_rule(clean_df, rule)
        return len(findings) == 0

adaptive_synthesizer = AdaptiveRuleSynthesizer()
