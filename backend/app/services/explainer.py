from datetime import datetime, timezone
import os
import re
from typing import List, Dict, Optional
from app.models.finding import Finding
from app.models.explanation import (
    Explanation, OperationHintType, MCPActionBlueprint, PolyglotRegexInfo
)
from app.utils.pii_masker import mask_pii_dict

def _infer_core_triad_regex(columns: List[str], metadata: dict) -> Optional[PolyglotRegexInfo]:
    col_text = " ".join(columns).lower()
    if any(k in col_text for k in ["phone", "mobile", "tel", "contact"]):
        return PolyglotRegexInfo(
            domain="phone",
            target_locales=["US", "UK", "IN", "E.164"],
            regex_pattern=r"^(\+?[1-9]\d{1,14}|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+91[-.\s]?\d{10})$",
            description="Matches international E.164 (+prefix), US (XXX) XXX-XXXX, and Indian +91 10-digit formats."
        )
    elif any(k in col_text for k in ["zip", "postal", "pin", "pincode"]):
        return PolyglotRegexInfo(
            domain="postal_code",
            target_locales=["US", "UK", "IN"],
            regex_pattern=r"^(\d{5}(-\d{4})?|[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}|\d{6})$",
            description="Matches US 5/9 digit ZIP, UK alphanumeric postcodes, and Indian 6-digit PIN codes."
        )
    elif any(k in col_text for k in ["date", "time", "dob", "created_at"]):
        return PolyglotRegexInfo(
            domain="date",
            target_locales=["ISO-8601", "EU (DD/MM/YYYY)", "US (MM/DD/YYYY)"],
            regex_pattern=r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$",
            description="Matches ISO-8601 YYYY-MM-DD, European DD/MM/YYYY, and US MM/DD/YYYY formats."
        )
    return None

def generate_deterministic_fallback(finding: Finding) -> Explanation:
    col_str = ", ".join(finding.affected_columns)
    first_col = finding.affected_columns[0] if finding.affected_columns else "target"

    poly_regex = _infer_core_triad_regex(finding.affected_columns, finding.metadata)
    rec_regex = poly_regex.regex_pattern if poly_regex else None

    if finding.issue_family == "missing":
        text = f"Column '{col_str}' contains missing or empty values affecting {len(finding.affected_row_indices)} rows."
        impact = "Downstream aggregations, KPI dashboards, and ML models may silently drop rows or skew calculations."
        action = f"Consider imputing missing values with column median/mode or filling with an approved business default."
        hint: OperationHintType = "fill_missing"
        pandas_code = f"df['{first_col}'] = df['{first_col}'].fillna('N/A')"
        mcp = MCPActionBlueprint(
            tool_name="fill_missing_values",
            parameters={"column": first_col, "strategy": "default_value", "default": "N/A"},
            business_summary=f"Replaces empty cells in {first_col} with a standard placeholder.",
            risk_level="medium",
            rollback_action={"tool_name": "restore_column", "parameters": {"column": first_col}}
        )
    elif finding.issue_family == "duplicate":
        text = f"Duplicate records detected affecting {len(finding.affected_row_indices)} rows across columns: {col_str}."
        impact = "Duplicates distort transactional totals, overstate revenue, and skew customer counts."
        action = "Review duplicate row pairs and deduplicate or flag repeated business keys."
        hint = "review_only"
        pandas_code = f"df = df.drop_duplicates(subset={finding.affected_columns}, keep='first')"
        mcp = MCPActionBlueprint(
            tool_name="deduplicate_records",
            parameters={"strategy": "drop_exact_duplicates", "keep": "first"},
            business_summary="Drops redundant identical rows while preserving primary transactions.",
            risk_level="high",
            rollback_action={"tool_name": "restore_rows", "parameters": {"indices": finding.affected_row_indices[:5]}}
        )
    elif finding.issue_family == "outlier":
        text = f"Statistically extreme outlier values observed in column '{col_str}' detected by {', '.join(finding.detection_methods)}."
        impact = "Outliers may be data entry mistakes or legitimate high-value transactions; unhandled, they distort statistical metrics."
        action = "Inspect affected rows to verify whether values reflect genuine anomalies or erroneous units."
        hint = "review_only"
        pandas_code = f"q1 = df['{first_col}'].quantile(0.25)\nq3 = df['{first_col}'].quantile(0.75)\niqr = q3 - q1\ndf = df[~((df['{first_col}'] < q1 - 1.5 * iqr) | (df['{first_col}'] > q3 + 1.5 * iqr))]"
        mcp = MCPActionBlueprint(
            tool_name="flag_for_review",
            parameters={"column": first_col, "row_indices": finding.affected_row_indices[:10]},
            business_summary="Flags extreme statistical deviations for operational auditor review.",
            risk_level="low",
            rollback_action={"tool_name": "clear_review_flags", "parameters": {"column": first_col}}
        )
    elif finding.issue_family == "inconsistent":
        candidate = finding.metadata.get("canonical_candidate", "standard form")
        text = f"Categorical spelling or casing inconsistencies found in '{col_str}'. Candidate standard is '{candidate}'."
        impact = "Splits reports across separate groups (e.g. 'Mumbai' vs 'mumbai'), breaking category rollups."
        action = f"Normalize text casing and map variant spellings to canonical '{candidate}'."
        hint = "case_normalization"
        pandas_code = f"df['{first_col}'] = df['{first_col}'].astype(str).str.strip().str.title()"
        mcp = MCPActionBlueprint(
            tool_name="normalize_casing_and_whitespace",
            parameters={"column": first_col, "target_canonical": candidate},
            business_summary=f"Standardizes casing and trims irregular spacing in {first_col} to match '{candidate}'.",
            risk_level="low",
            rollback_action={"tool_name": "restore_column", "parameters": {"column": first_col}}
        )
    elif finding.issue_family == "arithmetic_conflict":
        formula = finding.metadata.get("formula", "quantity * unit_price == total_amount")
        text = f"Cross-column calculation discrepancy detected where {formula} beyond currency cent tolerance (±0.01)."
        impact = "Produces inaccurate financial reconciliation totals, incorrect customer invoices, and audit flags."
        action = "Review line-item calculation discrepancies and recalculate totals or verify unrecorded discounts."
        hint = "review_only"
        pandas_code = "mask = abs(df['total_amount'] - (df['quantity'] * df['unit_price'])) > 0.01\ndf.loc[mask, 'total_amount'] = df.loc[mask, 'quantity'] * df.loc[mask, 'unit_price']"
        mcp = MCPActionBlueprint(
            tool_name="recalculate_column",
            parameters={"formula": formula, "affected_rows": finding.affected_row_indices[:10]},
            business_summary="Recalculates line item totals using verified unit price and quantity values.",
            risk_level="medium",
            rollback_action={"tool_name": "restore_column", "parameters": {"column": finding.affected_columns[-1] if finding.affected_columns else "total"}}
        )
    else:
        text = f"Data quality irregularity observed in column '{col_str}'."
        impact = "May impact reporting reliability."
        action = "Manual inspection recommended."
        hint = "review_only"
        pandas_code = f"# Review column '{col_str}'\nprint(df['{first_col}'].describe())"
        mcp = MCPActionBlueprint(
            tool_name="flag_for_review",
            parameters={"columns": finding.affected_columns},
            business_summary="Marks irregular rows for manual verification.",
            risk_level="low",
            rollback_action={"tool_name": "noop", "parameters": {}}
        )

    # If polyglot regex was inferred, populate it
    if not poly_regex and "regex" in col_str.lower():
        poly_regex = PolyglotRegexInfo(
            domain="general",
            target_locales=["Universal"],
            regex_pattern=r"^[A-Za-z0-9_\-\.\s]+$",
            description="Universal alphanumeric string validation pattern."
        )

    return Explanation(
        finding_id=str(finding.finding_id),
        is_ai_generated=False,
        explanation_text=text,
        business_impact=impact,
        recommended_action=action,
        recommended_regex=rec_regex,
        polyglot_regex=poly_regex,
        mcp_action=mcp,
        pandas_code=pandas_code,
        operation_hint=hint,
        requires_approval=True,
        generated_at=datetime.now(timezone.utc)
    )

class ExplainerService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    @property
    def enabled(self) -> bool:
        api_key = os.getenv("GEMINI_API_KEY") or self.api_key
        provider = os.getenv("LLM_PROVIDER", "")
        return bool(api_key and provider not in ("disabled", None, ""))

    def explain_finding(self, finding: Finding) -> Explanation:
        """Synchronous single-finding explanation generator."""
        return generate_deterministic_fallback(finding)

    async def explain_findings(self, findings: List[Finding]) -> Dict[str, Explanation]:
        explanations = {}
        api_key = os.getenv("GEMINI_API_KEY") or self.api_key
        is_active = self.enabled
        for finding in findings:
            fid = str(finding.finding_id)
            if not is_active:
                explanations[fid] = generate_deterministic_fallback(finding)
                continue

            try:
                masked_examples = [mask_pii_dict(r) for r in finding.example_rows]
                prompt = (
                    f"Explain this data quality finding concisely in plain language for a non-technical business reader.\n"
                    f"Issue Family: {finding.issue_family}\n"
                    f"Columns: {', '.join(finding.affected_columns)}\n"
                    f"Affected Rows Count: {len(finding.affected_row_indices)}\n"
                    f"Severity: {finding.severity}\n"
                    f"Example rows: {masked_examples}\n"
                    f"Metadata: {finding.metadata}\n\n"
                    f"Respond in valid JSON with keys: explanation, business_impact, recommended_action, pandas_code (executable pandas snippet to remediate the issue), operation_hint "
                    f"(one of: 'trim_whitespace', 'case_normalization', 'map_category', 'fill_missing', 'review_only'), "
                    f"mcp_tool_name, mcp_risk_level ('low', 'medium', 'high'), recommended_regex (if applicable)."
                )
                
                raw_text = None
                # Method A: Direct HTTPS REST API using requests (zero external SDK dependencies)
                try:
                    import requests
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.2}
                    }
                    resp = requests.post(url, json=payload, headers=headers, timeout=12)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                except Exception:
                    pass

                # Method B: Fallback to google.generativeai if installed
                if not raw_text:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(prompt)
                        raw_text = response.text
                    except Exception:
                        pass

                if not raw_text:
                    explanations[fid] = generate_deterministic_fallback(finding)
                    continue

                import json
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                parsed = json.loads(cleaned_text.strip())

                poly = _infer_core_triad_regex(finding.affected_columns, finding.metadata)
                rec_reg = parsed.get("recommended_regex") or (poly.regex_pattern if poly else None)

                mcp = MCPActionBlueprint(
                    tool_name=parsed.get("mcp_tool_name", "remediate_finding"),
                    parameters={"columns": finding.affected_columns},
                    business_summary=parsed.get("recommended_action", "Apply proposed remediation"),
                    risk_level=parsed.get("mcp_risk_level", "low"),
                    rollback_action={"tool_name": "restore_column", "parameters": {"columns": finding.affected_columns}}
                )
                
                explanations[fid] = Explanation(
                    finding_id=fid,
                    is_ai_generated=True,
                    explanation_text=parsed.get("explanation", ""),
                    business_impact=parsed.get("business_impact", ""),
                    recommended_action=parsed.get("recommended_action", ""),
                    recommended_regex=rec_reg,
                    polyglot_regex=poly,
                    mcp_action=mcp,
                    pandas_code=parsed.get("pandas_code"),
                    operation_hint=parsed.get("operation_hint", "review_only"),
                    requires_approval=True,
                    generated_at=datetime.now(timezone.utc)
                )
            except Exception:
                explanations[fid] = generate_deterministic_fallback(finding)

        return explanations

explainer_service = ExplainerService()
