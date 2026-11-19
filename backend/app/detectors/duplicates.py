import re
import uuid
from typing import List, Optional, Tuple
import pandas as pd
from app.detectors.base import BaseDetector, clean_records_for_json
from app.models.finding import Finding

class DuplicateDetector(BaseDetector):
    def infer_keys(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """
        Infers candidate Primary Key and Customer/Entity Key from column names and cardinality.
        """
        primary_key = None
        entity_key = None

        pk_pattern = re.compile(r"(?i).*(order_id|txn_id|transaction_id|invoice_id|^id$|order_number)")
        entity_pattern = re.compile(r"(?i).*(customer|user|client|email|phone|buyer|cust_id)")

        # 1. Primary Key heuristic
        candidates_pk = []
        for col in df.columns:
            if pk_pattern.match(col):
                candidates_pk.append(col)
            elif col.lower().endswith("_id"):
                candidates_pk.append(col)

        if candidates_pk:
            # Pick candidate with highest uniqueness ratio
            candidates_pk.sort(key=lambda c: df[c].nunique() / max(len(df), 1), reverse=True)
            primary_key = candidates_pk[0]
        else:
            # Look for any high-cardinality ID column
            for col in df.columns:
                if "id" in col.lower() and df[col].nunique() / max(len(df), 1) > 0.8:
                    primary_key = col
                    break

        # 2. Entity Key heuristic
        for col in df.columns:
            if col != primary_key and entity_pattern.match(col):
                entity_key = col
                break

        return primary_key, entity_key

    def detect(
        self,
        df: pd.DataFrame,
        primary_key: Optional[str] = None,
        entity_key: Optional[str] = None
    ) -> List[Finding]:
        findings: List[Finding] = []
        if len(df) == 0:
            return findings

        # Auto-infer keys if not explicitly supplied
        inferred_pk, inferred_ek = self.infer_keys(df)
        pk = primary_key or inferred_pk
        ek = entity_key or inferred_ek

        # 1. Tier A: Exact Duplicate Rows (Auto-Drop Candidate)
        exact_dupes_mask = df.duplicated(keep=False)
        exact_indices = df.index[exact_dupes_mask].tolist()

        if exact_indices:
            exact_count = len(exact_indices)
            sample_rows = clean_records_for_json(df.loc[exact_indices[:5]].to_dict(orient="records"))
            findings.append(Finding(
                finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"exact_duplicates_{exact_count}"),
                issue_family="duplicate",
                affected_columns=list(df.columns),
                affected_row_indices=exact_indices,
                severity="warning",
                detection_methods=["exact_hash"],
                example_rows=sample_rows,
                metadata={
                    "tier": "tier_a",
                    "classification": "exact_duplicate",
                    "action": "auto_drop",
                    "match_type": "exact",
                    "duplicate_count": exact_count,
                    "duplicate_groups": int(exact_count / 2),
                    "description": "Exact duplicate rows identical in payload; safely droppable automatically."
                }
            ))

        # 2. Tier B: Primary Key Conflict Detection / ID Collisions (Manual Review Required)
        # Rows sharing the primary key but differing across other columns are critical key conflicts
        if pk and pk in df.columns:
            key_dupes_mask = df.duplicated(subset=[pk], keep=False)
            conflicting_mask = key_dupes_mask & (~exact_dupes_mask)
            conflicting_indices = df.index[conflicting_mask].tolist()

            if conflicting_indices:
                sample_rows = clean_records_for_json(df.loc[conflicting_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"key_conflict_{pk}_{len(conflicting_indices)}"),
                    issue_family="duplicate",
                    affected_columns=[pk],
                    affected_row_indices=conflicting_indices,
                    severity="error",
                    detection_methods=["business_key_conflict"],
                    example_rows=sample_rows,
                    metadata={
                        "tier": "tier_b",
                        "classification": "id_collision",
                        "action": "manual_review",
                        "match_type": "business_key_conflict",
                        "primary_key": pk,
                        "conflict_count": len(conflicting_indices),
                        "description": "ID Collision: Distinct transactions assigned identical primary keys. Requires human review to prevent data loss."
                    }
                ))

        # 3. Tier C: Repeat Customers (Marked as 'Not an Issue')
        # Multiple records sharing entity_key (e.g. customer_name, email) with distinct primary_key
        # values represent legitimate repeat transactions and are classified as 'not an issue'.
        if ek and ek in df.columns:
            repeat_customer_indices = []
            customer_repeat_details = []
            grouped = df.groupby(ek)
            for cust_val, group in grouped:
                if len(group) > 1:
                    if (pk and pk in df.columns and group[pk].nunique() > 1) or len(group.drop_duplicates()) > 1:
                        repeat_customer_indices.extend(group.index.tolist())
                        customer_repeat_details.append({
                            "customer": str(cust_val),
                            "order_count": len(group),
                            "indices": group.index.tolist()
                        })
            if repeat_customer_indices:
                repeat_customer_indices = sorted(list(set(repeat_customer_indices)))
                sample_rows = clean_records_for_json(df.loc[repeat_customer_indices[:5]].to_dict(orient="records"))
                findings.append(Finding(
                    finding_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"repeat_customer_{ek}_{len(repeat_customer_indices)}"),
                    issue_family="duplicate",
                    affected_columns=[ek],
                    affected_row_indices=repeat_customer_indices,
                    severity="info",
                    detection_methods=["relational_entity_tracking"],
                    example_rows=sample_rows,
                    metadata={
                        "tier": "tier_c",
                        "classification": "repeat_customer",
                        "status": "not_an_issue",
                        "action": "none",
                        "customer_key": ek,
                        "customer_name": customer_repeat_details[0]["customer"] if customer_repeat_details else "",
                        "repeat_count": len(repeat_customer_indices),
                        "repeat_customers": customer_repeat_details[:5],
                        "description": "Legitimate repeat customer purchases across multiple dates or distinct orders. Marked as 'Not an Issue' / business as usual."
                    }
                ))

        return findings
