import uuid
from typing import List, Dict
import pandas as pd
from rapidfuzz import process, fuzz
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

class InconsistentValueDetector(BaseDetector):
    def __init__(self, threshold: int = 85):
        self.threshold = threshold

    def detect(self, df: pd.DataFrame) -> List[Finding]:
        findings: List[Finding] = []
        if len(df) == 0:
            return findings

        # Check categorical / text columns
        object_cols = df.select_dtypes(include=["object", "string"]).columns

        for col in object_cols:
            series = df[col].dropna().astype(str).str.strip()
            if series.nunique() <= 1 or series.nunique() > 100:
                # Skip trivial or high-cardinality free text
                continue

            # Normalized representation mapping: lowercase -> list of original distinct variants
            distinct_values = series.unique()
            value_counts = series.value_counts()
            
            # Group by case/space normalization
            normalized_groups: Dict[str, List[str]] = {}
            for val in distinct_values:
                key = " ".join(val.lower().split())
                normalized_groups.setdefault(key, []).append(val)

            # Find near-matches across distinct canonical keys using RapidFuzz
            processed_keys = set()
            keys = list(normalized_groups.keys())

            for i, key1 in enumerate(keys):
                if key1 in processed_keys:
                    continue
                matched_variants = set(normalized_groups[key1])
                
                # Check fuzzy similarities with remaining keys
                for key2 in keys[i+1:]:
                    sim = fuzz.WRatio(key1, key2)
                    if sim >= self.threshold:
                        matched_variants.update(normalized_groups[key2])
                        processed_keys.add(key2)

                if len(matched_variants) > 1:
                    # Inconsistency found! Determine canonical candidate:
                    # 1. Highest frequency count
                    # 2. Prefer form without internal spaces (e.g. "Mumbai" > "mumb ai")
                    # 3. Prefer Title Case over lowercase
                    def canonical_score(v: str):
                        cnt = value_counts.get(v, 0)
                        space_pen = -1 if " " in v.strip() else 0
                        case_score = 2 if v == v.title() else (1 if v.islower() else 0)
                        return (cnt, space_pen, case_score)

                    canonical_candidate = max(matched_variants, key=canonical_score)
                    affected_mask = df[col].astype(str).str.strip().isin(matched_variants)
                    affected_indices = df.index[affected_mask].tolist()

                    sample_rows = clean_records_for_json(df.loc[affected_indices[:5]].to_dict(orient="records"))
                    findings.append(Finding(
                        finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{col}_inconsistent_{canonical_candidate}"),
                        issue_family="inconsistent",
                        affected_columns=[col],
                        affected_row_indices=affected_indices,
                        severity="warning",
                        detection_methods=["normalization", "rapidfuzz_wratio"],
                        example_rows=sample_rows,
                        metadata={
                            "canonical_candidate": canonical_candidate,
                            "normalized_variants": sorted(list(matched_variants)),
                            "similarity_threshold": self.threshold
                        }
                    ))
                    processed_keys.add(key1)

        return findings
