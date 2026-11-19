import os
import json
import re
import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
from app.detectors.base import clean_records_for_json
from app.detectors.missing import MissingValueDetector
from app.detectors.duplicates import DuplicateDetector
from app.detectors.outliers import OutlierDetector
from app.detectors.inconsistent import InconsistentValueDetector
from app.detectors.validation import ArithmeticValidationDetector
from app.detectors.validity import ValidityDetector
from app.models.finding import Finding

DEFAULT_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "custom_rules.json")

class DetectorRegistry:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or DEFAULT_STORAGE_PATH
        self.custom_rules: List[Dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.custom_rules = data
            except Exception:
                self.custom_rules = []
        else:
            self.custom_rules = []

    def _save_rules(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.custom_rules, f, indent=2)
        except Exception:
            pass

    def get_builtin_detectors(self) -> List[Any]:
        return [
            MissingValueDetector(),
            DuplicateDetector(),
            OutlierDetector(),
            InconsistentValueDetector(),
            ArithmeticValidationDetector(),
            ValidityDetector()
        ]

    def get_custom_rules(self) -> List[Dict[str, Any]]:
        return self.custom_rules

    def register_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        # Deduplicate by rule_id
        rule_id = rule.get("rule_id", f"rule_{uuid.uuid4().hex[:8]}")
        rule["rule_id"] = rule_id
        self.custom_rules = [r for r in self.custom_rules if r.get("rule_id") != rule_id]
        self.custom_rules.append(rule)
        self._save_rules()
        return rule

    def run_custom_rule(self, df: pd.DataFrame, rule: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        target_cols = rule.get("target_columns", [])
        pattern = rule.get("pattern") or rule.get("anomaly_pattern", "")
        pattern_type = rule.get("pattern_type", "anomaly_regex")  # 'regex_match' vs 'anomaly_regex'

        for col in target_cols:
            if col not in df.columns:
                continue

            invalid_indices = []
            compiled_re = None
            if pattern:
                try:
                    compiled_re = re.compile(pattern)
                except Exception:
                    compiled_re = None

            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "":
                    continue
                val_str = str(val).strip()

                if pattern_type == "regex_match":
                    # Value MUST match the valid pattern; if not matching, flag!
                    if compiled_re and not compiled_re.match(val_str):
                        invalid_indices.append(idx)
                else:
                    # Value matches known anomaly pattern (or keyword); if matching, flag!
                    if compiled_re:
                        if compiled_re.search(val_str):
                            invalid_indices.append(idx)
                    elif pattern in val_str:
                        invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{rule['rule_id']}_{col}_{len(invalid_indices)}"),
                    issue_family="novel_anomaly",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity=rule.get("severity", "warning"),
                    detection_methods=["synthesized_adaptive_rule"],
                    example_rows=sample_rows,
                    metadata={
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("rule_name", "Novel Anomaly Rule"),
                        "description": rule.get("description", "Dynamically synthesized anomaly rule."),
                        "pattern": pattern,
                        "remediation_code": rule.get("remediation_code", "")
                    }
                ))

        return findings

    def run_all(
        self,
        df: pd.DataFrame,
        primary_key: Optional[str] = None,
        entity_key: Optional[str] = None,
        outlier_iqr_multiplier: float = 1.5,
        fuzzy_threshold: int = 85,
        arithmetic_tolerance: float = 0.01
    ) -> List[Finding]:
        all_findings = []
        if len(df) == 0:
            return all_findings

        # 1. Built-in detectors
        missing_det = MissingValueDetector()
        dupes_det = DuplicateDetector()
        outlier_det = OutlierDetector(iqr_multiplier=outlier_iqr_multiplier)
        inconsistent_det = InconsistentValueDetector(threshold=fuzzy_threshold)
        arithmetic_det = ArithmeticValidationDetector(tolerance=arithmetic_tolerance)
        validity_det = ValidityDetector()

        inferred_pk, inferred_ek = dupes_det.infer_keys(df)
        active_pk = primary_key or inferred_pk
        active_ek = entity_key or inferred_ek

        all_findings.extend(missing_det.detect(df))
        all_findings.extend(dupes_det.detect(df, primary_key=active_pk, entity_key=active_ek))
        all_findings.extend(outlier_det.detect(df))
        all_findings.extend(inconsistent_det.detect(df))
        all_findings.extend(arithmetic_det.detect(df, tolerance=arithmetic_tolerance))
        all_findings.extend(validity_det.detect(df))

        # 2. Dynamic custom rules
        for rule in self.custom_rules:
            if rule.get("is_active", True):
                all_findings.extend(self.run_custom_rule(df, rule))

        return all_findings

detector_registry = DetectorRegistry()
