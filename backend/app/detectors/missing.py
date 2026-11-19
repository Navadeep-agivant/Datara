import uuid
from typing import List, Set
import pandas as pd
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

DEFAULT_MISSING_TOKENS: Set[str] = {
    "", "na", "n/a", "null", "none", "?", "-", "unknown", "nan", "nil"
}

class MissingValueDetector(BaseDetector):
    def __init__(self, missing_tokens: Set[str] = None):
        self.missing_tokens = missing_tokens or DEFAULT_MISSING_TOKENS

    def detect(self, df: pd.DataFrame) -> List[Finding]:
        findings: List[Finding] = []
        total_rows = len(df)
        if total_rows == 0:
            return findings

        for col in df.columns:
            series = df[col]
            # Native nulls
            native_mask = series.isna()
            
            # String sentinel tokens
            text_series = series.astype(str).str.strip().str.lower()
            token_mask = text_series.isin(self.missing_tokens)
            
            combined_mask = native_mask | token_mask
            affected_indices = df.index[combined_mask].tolist()
            null_count = len(affected_indices)

            if null_count > 0:
                null_pct = round((null_count / total_rows) * 100, 2)
                severity = "error" if null_pct > 10.0 else "warning" if null_pct > 2.0 else "info"
                
                # Sample rows (sanitized of NaN/inf for JSON)
                sample_rows = clean_records_for_json(df.loc[affected_indices[:5]].to_dict(orient="records"))
                
                # Found tokens
                found_tokens = list(set(text_series[token_mask].unique()) - {"nan"})

                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{col}_missing_{null_count}"),
                    issue_family="missing",
                    affected_columns=[col],
                    affected_row_indices=affected_indices,
                    severity=severity,
                    detection_methods=["null_and_sentinel_token_scan"],
                    example_rows=sample_rows,
                    metadata={
                        "null_count": null_count,
                        "null_pct": null_pct,
                        "sentinel_tokens_found": found_tokens
                    }
                ))

        return findings
