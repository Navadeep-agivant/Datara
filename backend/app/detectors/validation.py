import re
import uuid
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

class ArithmeticValidationDetector(BaseDetector):
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def _find_arithmetic_triad(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        qty_pattern = re.compile(r"(?i).*(qty|quantity|units?|count)$")
        price_pattern = re.compile(r"(?i).*(unit_price|price|rate|cost)$")
        total_pattern = re.compile(r"(?i).*(total_amount|total|subtotal|line_total|final_amount)$")

        qty_col = None
        price_col = None
        total_col = None

        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            if qty_pattern.match(col) and not qty_col:
                qty_col = col
            elif price_pattern.match(col) and not price_col:
                price_col = col
            elif total_pattern.match(col) and not total_col:
                total_col = col

        return qty_col, price_col, total_col

    def detect(self, df: pd.DataFrame, tolerance: Optional[float] = None) -> List[Finding]:
        findings: List[Finding] = []
        if len(df) == 0:
            return findings

        tol = tolerance if tolerance is not None else self.tolerance
        qty_col, price_col, total_col = self._find_arithmetic_triad(df)

        if not (qty_col and price_col and total_col):
            return findings

        # Drop rows where any of the three are NaN for arithmetic check
        valid_mask = df[qty_col].notna() & df[price_col].notna() & df[total_col].notna()
        sub_df = df[valid_mask]

        if len(sub_df) == 0:
            return findings

        expected_total = sub_df[qty_col] * sub_df[price_col]
        diff = (expected_total - sub_df[total_col]).abs()

        # Check tolerance (currency cent threshold 0.01)
        inconsistent_mask = diff > tol
        inconsistent_indices = sub_df.index[inconsistent_mask].tolist()

        if inconsistent_indices:
            sample_rows = clean_records_for_json(df.loc[inconsistent_indices[:5]].to_dict(orient="records"))
            findings.append(Finding(
                finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"arithmetic_mismatch_{total_col}_{len(inconsistent_indices)}"),
                issue_family="arithmetic_conflict",
                affected_columns=[qty_col, price_col, total_col],
                affected_row_indices=inconsistent_indices,
                severity="error",
                detection_methods=["cross_column_arithmetic"],
                example_rows=sample_rows,
                metadata={
                    "formula": f"{qty_col} * {price_col} == {total_col}",
                    "tolerance": tol,
                    "discrepancy_count": len(inconsistent_indices),
                    "discrepant_indices": inconsistent_indices[:10]
                }
            ))

        return findings
