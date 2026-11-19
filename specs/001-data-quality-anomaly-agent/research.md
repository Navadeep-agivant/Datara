# Research: AI Data Quality & Anomaly Detection Agent

**Phase**: 0 — Outline & Research  
**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Last Updated**: 2026-11-19 (Aligned with Constitution v1.3.0)

---

## R-001: Session State Management (In-Memory Scope)

**Decision**: In-process thread-safe dictionary keyed by UUID4 session ID.
- Stores immutable original DataFrame (`original_df`) alongside mutable `working_df`.
- Supports up to 50,000 rows in memory with low CPU/RAM overhead.
- No database or Redis required for single-node / local demo environments.

---

## R-002: Relational Deduplication & 3-Tier Classification

**Decision**: Disambiguate multi-order customer activity from corrupt duplicate transactions.
- **Tier A (Exact Duplicates)**: Identical values across *all* columns flagged as redundant rows, marked for automatic safe dropping.
- **Tier B (ID / Primary Key Collisions)**: If the primary key `order_id` is repeated with *conflicting* line items (different quantities, prices, or dates), flag as a high-severity entity conflict routed to manual review to prevent data loss.
- **Tier C (Repeat Customers)**: Group by customer identifiers (`customer_name`, `email`, `phone`). If distinct `order_date` or `order_id` values exist for that customer entity, surface explicitly in the UI as "not an issue" / business as usual (0 score deduction).

---

## R-003: Two-Tier Anomaly Engine & Rule-Based Validity

**Decision**:
- **Tier 1 (Deterministic Baseline Engine)**:
  - Missing values: scan for SQL nulls, empty strings, whitespace, and sentinels (`N/A`, `unknown`, `-`).
  - Rule-Based Validity Detector: Explicit dayfirst date parsing (`dayfirst=True`) catching impossible dates (e.g. `2026-02-30`), dummy phones (`0000000000`), email syntax, rating bounds ($[1.0, 5.0]$), delivery days ($\ge 0$), and positive quantity ($> 0$).
  - Outliers & Impossible Numbers: IQR (1.5×) + Modified Z-Score (MAD > 3.5), flagged for review rather than deleted.
  - Arithmetic consistency: exact cross-column check ($|\text{quantity} \times \text{unit\_price} - \text{total\_amount}| \le 0.01$).
  - Categoricals: Normalization (case-folding, space stripping) followed by RapidFuzz `WRatio` against dominant canonical candidates.
- **Tier 2 (Cognitive LLM Augmentation)**:
  - Takes Tier 1 structured findings and distinct token samples (never the raw dataset).
  - Translates statistical findings into non-technical executive language.
  - Suggests polyglot regex patterns for complex formats (e.g. international phone prefixes `+91`, variable spacing).
  - Outlines MCP-ready structured remediation proposals.
  - PII masking strictly enforced before prompt transmission.

---

## R-004: Quality Scoring Model & Calibrated Weights

**Decision**: Transparent deduction-based formula:
$$\text{overall\_score} = \max\left(0.0, 100.0 - \sum \text{points\_deducted}\right)$$
- Calibrated weights: Arithmetic (2.0), Invalid (1.5), Missing (1.0), Duplicate (1.0), Inconsistent (0.5), Repeat Customer (0.0).
- Recomputed live when operations are approved or undone in the Cleaning Studio.
- Fully transparent and displayed directly in the app UI and report.

---

## R-005: Safe Remediation & CSV Formula Injection Prevention

**Decision**:
- Non-destructive: transformations apply exclusively to the working copy.
- Honest remediation: `total_amount` is recomputed as $\text{quantity} \times \text{unit\_price}$; `rating`, `email`, and `phone` are preserved as `null`/empty and flagged for human review (never imputed with synthetic placeholders).
- FormulaGuard: neutralizes spreadsheet formula execution exploits (`=`, `+`, `-`, `@`) with prepended `'` on export.
- LIFO undo stack restores previous cell snapshots.

---

## R-006: Core Triad Polyglot Regex Engine

**Decision**: Standardize on three universal multi-format regex families:
1. **Phones**: International E.164 (`^\+?[1-9]\d{1,14}$`), US standard (`^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$`), and Indian (`^(?:\+91|91|0)?[6-9]\d{9}$`).
2. **Postal Codes**: US ZIP (`^\d{5}(?:-\d{4})?$`), UK outward/inward, and Indian PIN (`^[1-9][0-9]{5}$`).
3. **Dates**: ISO-8601 (`^\d{4}-\d{2}-\d{2}$`), European (`^\d{2}/\d{2}/\d{4}$`), and US (`^\d{2}/\d{2}/\d{4}$`).

---

## R-007: Standard MCP Action Blueprint Schema

**Decision**: Expose structured JSON schemas ready for agentic execution sidecars:
```json
{
  "tool_name": "clean_anomaly",
  "parameters": { "column": "col_name", "action": "normalize_casing" },
  "risk_level": "low",
  "rollback_action": { "tool_name": "restore_column", "parameters": { "column": "col_name" } }
}
```

---

## R-008: Interactive Visual Sandbox & Always-Code Transparency

**Decision**: Complete visual diff sandbox with mandatory executable code:
- **Sandbox Diff View**: Side-by-side or cell-level diff displaying original vs cleaned values with distinct color coding.
- **Always-Code Generation**: Every proposed or executed operation includes an exact, executable Python/pandas code block that performs the mutation, allowing data engineers to inspect or run the transformation outside the platform without vendor lock-in.
- **Approval Gate**: Changes are provisional until approved by the user (single-operation click or verified safe batch clean).

---

## R-009: Adaptive Novel Anomaly Discovery & Self-Evolving Rule Engine

**Decision**: Autonomous discovery and dynamic codebase evolution:
- **Novel Anomaly Identification**: When the CSV contains an error pattern not covered by existing detectors, the AI agent uses cognitive heuristics to characterize the unscripted pattern.
- **Dynamic Rule Synthesis**: The agent generates deterministic detection code (regex, validation function, detector class) with automated unit test assertions.
- **Zero-False-Positive Safety Verification**: The synthesized rule is automatically evaluated against verified clean rows in the active dataset. If false positives are detected, the rule is refined or rejected.
- **Persistent Detector Registry**: Validated rules are dynamically registered in a persistent detector registry (`backend/app/detectors/registry.py` and persistent JSON/YAML definitions), ensuring the new rule is automatically active for all subsequent runs.
