import uuid
from typing import List
import pandas as pd
import numpy as np
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

class OutlierDetector(BaseDetector):
    def __init__(self, iqr_multiplier: float = 1.5):
        self.iqr_multiplier = iqr_multiplier

    def detect(self, df: pd.DataFrame) -> List[Finding]:
        findings: List[Finding] = []
        if len(df) < 4:
            return findings

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if series.nunique() <= 1:
                # Constant or empty column
                continue

            # Method 1: IQR
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            iqr_indices = set()
            if iqr > 0:
                lower_bound = q1 - (self.iqr_multiplier * iqr)
                upper_bound = q3 + (self.iqr_multiplier * iqr)
                iqr_mask = (series < lower_bound) | (series > upper_bound)
                iqr_indices = set(series[iqr_mask].index.tolist())

            # Method 2: Modified Z-Score using Median Absolute Deviation (MAD)
            mad_indices = set()
            median = float(series.median())
            mad = float((series - median).abs().median())
            if mad > 0:
                mod_z = 0.6745 * (series - median).abs() / mad
                mad_mask = mod_z > 3.5
                mad_indices = set(series[mad_mask].index.tolist())

            combined_indices = sorted(list(iqr_indices | mad_indices))
            if combined_indices:
                methods = []
                if iqr_indices:
                    methods.append("IQR")
                if mad_indices:
                    methods.append("MAD")

                # If flagged by both methods, severity is error; otherwise warning
                both_flagged = iqr_indices.intersection(mad_indices)
                severity = "error" if len(both_flagged) > 0 else "warning"

                sample_rows = clean_records_for_json(df.loc[combined_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{col}_outliers_{len(combined_indices)}"),
                    issue_family="outlier",
                    affected_columns=[col],
                    affected_row_indices=combined_indices,
                    severity=severity,
                    detection_methods=methods,
                    example_rows=sample_rows,
                    metadata={
                        "outlier_count": len(combined_indices),
                        "flagged_by_iqr_count": len(iqr_indices),
                        "flagged_by_mad_count": len(mad_indices),
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "median": median,
                        "mad": mad
                    }
                ))

        return findings
