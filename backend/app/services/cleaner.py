from datetime import datetime, timezone
import uuid
import re
from typing import List, Dict, Tuple, Optional
import pandas as pd
from app.models.cleaning import CleaningOperation, CellDiff, OperationType
from app.models.finding import Finding

class CleaningService:
    def generate_proposed_operations(self, findings: List[Finding]) -> List[CleaningOperation]:
        operations = []
        for f in findings:
            if f.is_resolved:
                continue

            # Legitimate repeat customers are not an issue
            if f.metadata.get("status") == "not_an_issue" or f.metadata.get("classification") == "repeat_customer":
                continue

            op_type: OperationType = "mark_for_review"
            risk_level = "low"
            bucket = "auto_fixable"
            affected_cols = f.affected_columns

            if f.issue_family == "arithmetic_conflict":
                op_type = "recalculate_arithmetic"
                risk_level = "low"
                bucket = "auto_fixable"
                # Focus operation on the total column that needs recalculation
                total_cols = [c for c in f.affected_columns if any(k in c.lower() for k in ["total", "amount"])]
                if total_cols:
                    affected_cols = total_cols
                else:
                    affected_cols = f.affected_columns[-1:]

            elif f.issue_family == "duplicate":
                if f.metadata.get("tier") == "tier_a" or f.metadata.get("classification") == "exact_duplicate":
                    op_type = "drop_exact_duplicate"
                    risk_level = "low"
                    bucket = "auto_fixable"
                else:
                    # Tier B: ID Collision / Primary Key conflict -> Must go to manual review
                    op_type = "mark_for_review"
                    risk_level = "high"
                    bucket = "needs_review"

            elif f.issue_family == "inconsistent":
                op_type = "case_normalization"
                risk_level = "low"
                bucket = "auto_fixable"

            elif f.issue_family == "missing":
                # Honest Remediation: Don't impute rating, email, or phone. Preserve nulls and flag.
                is_sensitive = any(k in c.lower() for c in f.affected_columns for k in ["rating", "email", "phone", "mobile", "tel", "contact"])
                is_total = any(k in c.lower() for c in f.affected_columns for k in ["total", "total_amount"])

                if is_sensitive:
                    op_type = "mark_for_review"
                    risk_level = "medium"
                    bucket = "needs_review"
                elif is_total:
                    op_type = "recalculate_arithmetic"
                    risk_level = "low"
                    bucket = "auto_fixable"
                else:
                    op_type = "fill_missing"
                    risk_level = "medium"
                    bucket = "auto_fixable"

            elif f.issue_family == "outlier":
                # Flag outliers, don't delete them. Show in needs human review bucket.
                op_type = "mark_for_review"
                risk_level = "low"
                bucket = "needs_review"

            elif f.issue_family == "novel_anomaly":
                op_type = "mark_for_review"
                risk_level = "medium"
                bucket = "needs_review"

            target_col = affected_cols[0] if affected_cols else "column"
            pandas_code = ""
            if op_type == "recalculate_arithmetic":
                pandas_code = f"df['{target_col}'] = (df['quantity'] * df['unit_price']).round(2)"
            elif op_type == "drop_exact_duplicate":
                pandas_code = "df = df.drop_duplicates(keep='first').reset_index(drop=True)"
            elif op_type == "case_normalization":
                canonical = f.metadata.get("canonical_candidate")
                if canonical:
                    pandas_code = f"df['{target_col}'] = df['{target_col}'].astype(str).str.strip().replace({{r'(?i)^{canonical}$': '{canonical}'}}, regex=True)"
                else:
                    pandas_code = f"df['{target_col}'] = df['{target_col}'].astype(str).str.strip().str.title()"
            elif op_type == "trim_whitespace":
                pandas_code = f"df['{target_col}'] = df['{target_col}'].astype(str).str.strip()"
            elif op_type == "fill_missing":
                pandas_code = f"df['{target_col}'] = df['{target_col}'].fillna('Not Provided')"
            else:
                if f.issue_family == "novel_anomaly" and f.metadata.get("remediation_code"):
                    pandas_code = f.metadata["remediation_code"]
                else:
                    pandas_code = f"# Review required for '{target_col}' without destructive overwrite"

            op = CleaningOperation(
                operation_id=uuid.uuid4(),
                finding_id=str(f.finding_id),
                operation_type=op_type,
                risk_level=risk_level,
                affected_columns=affected_cols,
                affected_row_indices=f.affected_row_indices,
                bucket=bucket,
                pandas_code=pandas_code,
                approval_status="pending"
            )
            operations.append(op)
        return operations

    def preview_operation(
        self,
        df: pd.DataFrame,
        op: CleaningOperation,
        finding: Optional[Finding] = None,
        include_unmutated: bool = False
    ) -> List[CellDiff]:
        diffs: List[CellDiff] = []

        # Exact arithmetic recalculation helper
        qty_col = next((c for c in df.columns if re.match(r"(?i).*(qty|quantity|units?|count)$", c)), None)
        price_col = next((c for c in df.columns if re.match(r"(?i).*(unit_price|price|rate|cost)$", c)), None)

        for idx in op.affected_row_indices:
            if idx not in df.index:
                continue
            for col in op.affected_columns:
                before_val = str(df.at[idx, col])
                after_val = before_val

                if op.operation_type == "case_normalization":
                    if finding and finding.metadata.get("canonical_candidate"):
                        after_val = finding.metadata["canonical_candidate"]
                    else:
                        after_val = before_val.strip().title()

                elif op.operation_type == "trim_whitespace":
                    after_val = before_val.strip()

                elif op.operation_type == "recalculate_arithmetic":
                    if qty_col and price_col and qty_col in df.columns and price_col in df.columns:
                        try:
                            q = float(df.at[idx, qty_col])
                            p = float(df.at[idx, price_col])
                            after_val = str(round(q * p, 2))
                        except Exception:
                            after_val = before_val

                elif op.operation_type == "drop_exact_duplicate":
                    after_val = "[DROPPED]"

                elif op.operation_type == "fill_missing":
                    # Never impute rating, email, or phone. Preserve null.
                    is_sensitive = any(k in col.lower() for k in ["rating", "email", "phone", "mobile", "tel"])
                    if is_sensitive:
                        after_val = before_val
                    elif pd.api.types.is_numeric_dtype(df[col]):
                        non_null = df[col].dropna()
                        if not non_null.empty:
                            median_val = float(non_null.median())
                            if (non_null % 1 == 0).all():
                                after_val = str(int(round(median_val)))
                            else:
                                after_val = str(round(median_val, 2))
                        else:
                            after_val = "0"
                    else:
                        after_val = "Not Provided"

                elif op.operation_type == "mark_for_review":
                    # Non-destructive: leave cell unmutated for manual review
                    after_val = before_val

                if include_unmutated or before_val != after_val:
                    diffs.append(CellDiff(
                        row_index=idx,
                        column_name=col,
                        before=before_val,
                        after=after_val
                    ))
        return diffs

    def regenerate_pandas_code_from_diffs(self, op: CleaningOperation) -> str:
        if not op.preview_diff:
            return op.pandas_code or ""
        lines = []
        for d in op.preview_diff:
            if d.after == "[DROPPED]":
                lines.append(f"df = df.drop(index=[{d.row_index}], errors='ignore')")
            elif d.after in ("None", "null", "nan", ""):
                lines.append(f"df.loc[{d.row_index}, '{d.column_name}'] = None")
            else:
                lines.append(f"df.loc[{d.row_index}, '{d.column_name}'] = {repr(d.after)}")
        return "\n".join(lines)

    def apply_operation(self, df: pd.DataFrame, op: CleaningOperation, diffs: List[CellDiff]) -> Tuple[pd.DataFrame, Dict]:
        original_records = {}

        if op.operation_type == "drop_exact_duplicate":
            # Keep first occurrence, drop subsequent duplicate rows
            exact_mask = df.duplicated(keep="first")
            indices_to_drop = [i for i in op.affected_row_indices if i in df.index and exact_mask.get(i, False)]
            if not indices_to_drop and len(op.affected_row_indices) > 1:
                indices_to_drop = [i for i in op.affected_row_indices[1:] if i in df.index]

            if indices_to_drop:
                dropped_df = df.loc[indices_to_drop].copy()
                original_records = {
                    "is_drop": True,
                    "dropped_indices": indices_to_drop,
                    "dropped_data": dropped_df.to_dict(orient="index")
                }
                df = df.drop(index=indices_to_drop)
        else:
            for diff in diffs:
                row_idx = diff.row_index
                col = diff.column_name
                if row_idx not in df.index:
                    continue
                if row_idx not in original_records:
                    original_records[row_idx] = {}
                original_records[row_idx][col] = df.at[row_idx, col]

                val_to_set = diff.after
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        if "." in str(val_to_set):
                            val_to_set = float(val_to_set)
                        else:
                            val_to_set = int(val_to_set)
                    except (ValueError, TypeError):
                        df[col] = df[col].astype(object)

                try:
                    df.at[row_idx, col] = val_to_set
                except Exception:
                    df[col] = df[col].astype(object)
                    df.at[row_idx, col] = val_to_set

        op.original_values = original_records
        op.applied_at = datetime.now(timezone.utc)
        op.approval_status = "approved"
        return df, original_records

    def apply_all_low_risk(
        self,
        df: pd.DataFrame,
        operations: List[CleaningOperation],
        findings_map: Optional[Dict[str, Finding]] = None
    ) -> Tuple[pd.DataFrame, List[CleaningOperation]]:
        findings_map = findings_map or {}
        applied = []
        for op in operations:
            if op.approval_status == "pending" and op.risk_level == "low" and op.bucket == "auto_fixable":
                finding = findings_map.get(op.finding_id)
                diffs = self.preview_operation(df, op, finding)
                if diffs or op.operation_type == "drop_exact_duplicate":
                    df, _ = self.apply_operation(df, op, diffs)
                    applied.append(op)
        return df, applied

    def undo_operation(self, df: pd.DataFrame, op: CleaningOperation) -> pd.DataFrame:
        if not op.original_values:
            op.approval_status = "pending"
            op.applied_at = None
            return df

        if op.original_values.get("is_drop"):
            dropped_data = op.original_values.get("dropped_data", {})
            if dropped_data:
                restored_df = pd.DataFrame.from_dict(dropped_data, orient="index")
                df = pd.concat([df, restored_df]).sort_index()
        else:
            for row_idx_str, col_vals in op.original_values.items():
                try:
                    row_idx = int(row_idx_str)
                except ValueError:
                    continue
                if row_idx in df.index:
                    for col, orig_val in col_vals.items():
                        try:
                            df.at[row_idx, col] = orig_val
                        except Exception:
                            df[col] = df[col].astype(object)
                            df.at[row_idx, col] = orig_val

        op.approval_status = "pending"
        op.applied_at = None
        return df

cleaning_service = CleaningService()
