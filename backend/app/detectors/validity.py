import re
import uuid
from typing import List, Optional, Set
import pandas as pd
import numpy as np
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

class ValidityDetector(BaseDetector):
    def __init__(self):
        self.email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$")
        self.dummy_phone_patterns = {
            "0000000000", "1111111111", "2222222222", "3333333333", "4444444444",
            "5555555555", "6666666666", "7777777777", "8888888888", "9999999999",
            "1234567890", "0123456789"
        }

    def detect(self, df: pd.DataFrame) -> List[Finding]:
        findings: List[Finding] = []
        if len(df) == 0:
            return findings

        # 1. Date Validity (explicit dayfirst=True, impossible dates, out of range)
        date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "created", "timestamp", "dob"])]
        for col in date_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null", "nat"]:
                    continue
                val_str = str(val).strip()
                try:
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", val_str):
                        parsed = pd.to_datetime(val_str, errors="coerce", format="%Y-%m-%d")
                    elif "/" in val_str or "-" in val_str:
                        parsed = pd.to_datetime(val_str, errors="coerce", dayfirst=True)
                    else:
                        parsed = pd.to_datetime(val_str, errors="coerce")

                    if pd.isna(parsed):
                        invalid_indices.append(idx)
                    else:
                        # Year range check (reasonable business bounds 1900 - 2050)
                        if parsed.year < 1900 or parsed.year > 2050:
                            invalid_indices.append(idx)
                except Exception:
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_date_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="error",
                    detection_methods=["dayfirst_date_parsing", "calendar_validity"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "dayfirst_explicit_date_parsing",
                        "invalid_count": len(invalid_indices),
                        "description": "Dates with impossible calendar days, invalid formats, or out of reasonable range."
                    }
                ))

        # 2. Phone Number Validity (format, length, dummy repetitive sequences)
        phone_cols = [c for c in df.columns if any(k in c.lower() for k in ["phone", "mobile", "tel", "cell", "contact"])]
        for col in phone_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                    continue
                val_str = str(val).strip()
                digits = re.sub(r"\D", "", val_str)
                # Flag if too short (< 7 digits), too long (> 15 digits), all same digits, or known dummy patterns
                if len(digits) < 7 or len(digits) > 15 or len(set(digits)) <= 1 or digits in self.dummy_phone_patterns:
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_phone_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="error",
                    detection_methods=["phone_format_and_repetition_check"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "valid_phone_format_and_sequence",
                        "invalid_count": len(invalid_indices),
                        "description": "Phone numbers with dummy repetitive digits (e.g. 0000000000) or invalid digit length."
                    }
                ))

        # 3. Email Validity (standard syntax, domain, and valid TLD)
        email_cols = [c for c in df.columns if "email" in c.lower() or (df[c].dropna().astype(str).str.contains("@").mean() > 0.3 if not df[c].dropna().empty else False)]
        for col in email_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                    continue
                val_str = str(val).strip()
                if not self.email_regex.match(val_str):
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_email_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="error",
                    detection_methods=["email_syntax_and_tld_check"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "valid_email_structure_and_tld",
                        "invalid_count": len(invalid_indices),
                        "description": "Email addresses with missing '@', malformed domains, or missing top-level domains."
                    }
                ))

        # 4. Rating Bounds [1.0, 5.0]
        rating_cols = [c for c in df.columns if any(k in c.lower() for k in ["rating", "stars"])]
        for col in rating_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                    continue
                try:
                    num_val = float(val)
                    if num_val < 1.0 or num_val > 5.0:
                        invalid_indices.append(idx)
                except (ValueError, TypeError):
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_rating_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="warning",
                    detection_methods=["rating_range_check"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "rating_between_1_and_5",
                        "bounds": "[1.0, 5.0]",
                        "invalid_count": len(invalid_indices),
                        "description": "Customer satisfaction ratings outside valid bounds [1.0, 5.0]."
                    }
                ))

        # 5. Delivery Days Non-Negative (>= 0)
        delivery_cols = [c for c in df.columns if any(k in c.lower() for k in ["delivery_days", "delivery_time", "transit_days", "shipping_days", "days_to_deliver"])]
        for col in delivery_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                    continue
                try:
                    num_val = float(val)
                    if num_val < 0:
                        invalid_indices.append(idx)
                except (ValueError, TypeError):
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_delivery_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="error",
                    detection_methods=["delivery_non_negative_check"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "delivery_days_non_negative",
                        "invalid_count": len(invalid_indices),
                        "description": "Delivery transit duration cannot be negative."
                    }
                ))

        # 6. Quantity Positive (> 0)
        qty_cols = [c for c in df.columns if re.match(r"(?i).*(qty|quantity|units?|count)$", c)]
        for col in qty_cols:
            invalid_indices = []
            for idx, val in df[col].items():
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                    continue
                try:
                    num_val = float(val)
                    if num_val <= 0:
                        invalid_indices.append(idx)
                except (ValueError, TypeError):
                    invalid_indices.append(idx)

            if invalid_indices:
                sample_rows = clean_records_for_json(df.loc[invalid_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"validity_qty_{col}_{len(invalid_indices)}"),
                    issue_family="invalid",
                    affected_columns=[col],
                    affected_row_indices=invalid_indices,
                    severity="error",
                    detection_methods=["quantity_positive_check"],
                    example_rows=sample_rows,
                    metadata={
                        "rule": "quantity_strictly_positive",
                        "invalid_count": len(invalid_indices),
                        "description": "Order quantities must be greater than zero."
                    }
                ))

        return findings
