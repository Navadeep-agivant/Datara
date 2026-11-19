# Quickstart Validation Guide

**Feature**: AI Data Quality & Anomaly Detection Agent
**Phase**: 1 — Design & Contracts
**Date**: 2026-11-18

This guide proves the feature works end-to-end. Follow these scenarios in order to validate each
user story independently before running the full integration test suite.

---

## Prerequisites

```
Python 3.11+
Node.js 20 LTS
An LLM provider API key in environment variable (see .env.example)
```

Setup:
```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/activate       # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in LLM_PROVIDER + API key

# Frontend
cd frontend
npm install

# Start both
cd backend && uvicorn app.main:app --reload &
cd frontend && npm run dev
```

---

## Scenario 1 — Upload & Profile (User Story 1, P1)

**Prerequisites**: Backend running on `localhost:8000`.

**Steps**:

```bash
# Upload the sample dataset
curl -s -F "file=@datasets/online_store_orders_sample.csv" \
  http://localhost:8000/upload | python -m json.tool
```

**Expected response**:
```json
{
  "session_id": "<uuid>",
  "filename": "online_store_orders_sample.csv",
  "row_count": <N>,
  "column_count": <M>,
  "encoding": "utf-8",
  "parse_warnings": []
}
```

```bash
# Retrieve profile (use session_id from above)
SESSION=<session_id>
curl -s http://localhost:8000/sessions/$SESSION/profile | python -m json.tool
```

**Expected**: JSON array with one `ColumnProfile` object per column. Each profile includes
`inferred_type`, `null_count`, `null_pct`, `unique_count`, `example_values`, and type-specific
stats. No column should have `inferred_type: "unknown"` for the sample dataset.

**Failure conditions**: HTTP 400 (file rejected), HTTP 500 (parse error), missing columns in
profile, `example_values` with more than 5 items.

---

## Scenario 2 — Rejection of Invalid Files (FR-001, FR-002)

```bash
# Empty file
echo "" > /tmp/empty.csv
curl -s -F "file=@/tmp/empty.csv" http://localhost:8000/upload

# Header-only file
echo "col1,col2" > /tmp/header_only.csv
curl -s -F "file=@/tmp/header_only.csv" http://localhost:8000/upload

# Wrong extension
curl -s -F "file=@docs/adr/some.txt" http://localhost:8000/upload
```

**Expected**: All three return HTTP 400 with a JSON `ErrorResponse` containing a specific
`error_code` and human-readable `message`. No 500 errors.

---

## Scenario 3 — Detection & Relational Deduplication Run (User Story 2, P1)

```bash
# Run all four detectors with relational deduplication and arithmetic tolerance
curl -s -X POST http://localhost:8000/sessions/$SESSION/detect \
  -H "Content-Type: application/json" \
  -d '{
    "primary_key": "order_id",
    "entity_key": "customer_name",
    "arithmetic_tolerance": 0.01,
    "outlier_iqr_multiplier": 1.5,
    "fuzzy_threshold": 85
  }' \
  | python -m json.tool
```

**Expected**:
- Response contains `findings` array; each finding has `finding_id`, `issue_family` (missing / duplicate / outlier / inconsistent), `affected_columns`, `affected_row_indices`, `severity`, `detection_methods`, and `example_rows` (≤ 5).
- `quality_score.overall_score` is between 0 and 100.
- **Relational Deduplication Validation**: Multiple orders from the same customer (e.g. "Rohan Sharma") on different dates are NOT flagged as duplicate orders. Only identical order IDs with conflicting items or identical full-row duplicates are flagged.
- **Arithmetic Check Validation**: Any rows where `abs(quantity * unit_price - total_amount) > 0.01` are flagged under arithmetic inconsistency with diff metadata.
- **Determinism check**: run the endpoint twice and confirm `findings` lists are identical (same `finding_id` values, same counts, same row indices).

---

## Scenario 4 — AI Explanations, Polyglot Regex & MCP Blueprints (User Story 3, P2)

```bash
curl -s http://localhost:8000/sessions/$SESSION/explain | python -m json.tool
```

**Expected**:
- One `Explanation` object per finding in the response dict.
- Each explanation has non-empty `explanation_text`, `business_impact`, `recommended_action`.
- **MCP Action Blueprint**: includes `mcp_action` with `tool_name`, `parameters`, `business_summary`, `risk_level` (`low`/`medium`/`high`), and `rollback_action`.
- **Polyglot Regex**: For phone, postal, or date format inconsistencies, `polyglot_regex` provides `domain`, `target_locales`, `regex_pattern`, and `description`.
- `requires_approval` is `true` for all explanations.

---

## Scenario 5 — Cleaning Workflow & Batch Safe Clean (User Story 4, P2)

```bash
# List proposed operations
curl -s http://localhost:8000/sessions/$SESSION/clean | python -m json.tool

# Preview the first operation
OP_ID=<first operation_id from above>
curl -s "http://localhost:8000/sessions/$SESSION/clean/preview?operation_id=$OP_ID" \
  | python -m json.tool
```

**Expected for preview**: `diff` array with `CellDiff` objects showing `before` and `after`
for every affected cell. The working dataset is NOT modified by the preview call.

```bash
# Batch Apply All Low-Risk operations (whitespace trimming, case normalization)
curl -s -X POST http://localhost:8000/sessions/$SESSION/clean/apply-all-low-risk | python -m json.tool
```

**Expected**: All operations with `risk_level: "low"` applied in a single batch; score recomputes immediately.

```bash
# Undo the operation
curl -s -X POST http://localhost:8000/sessions/$SESSION/clean/undo | python -m json.tool
```

**Expected**: `undone_operation_id` matches `$OP_ID`; score reverts to pre-apply value.

---

## Scenario 6 — Quality Score & Report Export (User Story 5, P3)

```bash
# Score endpoint
curl -s http://localhost:8000/sessions/$SESSION/score | python -m json.tool
```

**Expected**: `score_before.overall_score` and per-column scores are populated. `score_after` is
`null` if no cleaning has been applied.

```bash
# Download HTML report
curl -s http://localhost:8000/sessions/$SESSION/report -o /tmp/report.html
open /tmp/report.html    # or start /tmp/report.html on Windows
```

**Expected**: Valid HTML file opens in browser. Contains:
- Overall quality score (before / after if cleaning was applied)
- Per-column scores
- Finding summaries with example rows for each issue family
- Transformation log (may be empty if no cleaning)
- Timestamp and original filename

```bash
# Download cleaned CSV
curl -s http://localhost:8000/sessions/$SESSION/export/csv -o /tmp/cleaned.csv
```

**Expected**: Valid CSV. Inspect cells — no cell content beginning with `=`, `+`, `-`, `@`
should appear unescaped. Opening in Excel should not trigger a formula-injection warning.

---

## Scenario 7 — Performance Validation (SC-001, SC-006)

Use the full 10,000-row fixture (or generate one with the seed script in `datasets/`):

```bash
# Time the upload + profile
time curl -s -F "file=@datasets/large_10k_rows.csv" http://localhost:8000/upload

# Time detection
time curl -s -X POST http://localhost:8000/sessions/$SESSION/detect \
  -H "Content-Type: application/json" -d '{}'

# Time report generation
time curl -s http://localhost:8000/sessions/$SESSION/report -o /dev/null
```

**Expected**:
- Upload + profile: wall time ≤ 30 s (SC-001)
- Detection: wall time ≤ 30 s
- Report: wall time ≤ 15 s (SC-006)

---

## Scenario 8 — Adaptive Novel Anomaly Discovery & Dynamic Rule Synthesis (User Story 6, P2)

**Prerequisites**: Active session with an unscripted anomaly pattern.

**Steps**:
```bash
curl -s -X POST http://localhost:8000/sessions/$SESSION/adaptive-learn | python -m json.tool
```

**Expected response**:
```json
{
  "session_id": "<uuid>",
  "synthesized_rules": [
    {
      "rule_id": "rule_custom_error",
      "rule_name": "Custom Anomaly Detector",
      "anomaly_pattern": "...",
      "remediation_code": "df['col'] = ..."
    }
  ],
  "new_findings_count": 1,
  "message": "Synthesized 1 new detection rule and updated registry."
}
```

Inspection: The newly synthesized rule is permanently stored in `backend/app/detectors/custom_rules.json` and automatically executed in subsequent calls to `/sessions/{id}/detect`.

---

## Running the Automated Test Suite

```bash
cd backend

# Unit tests
pytest tests/unit/ -v --tb=short

# Integration tests
pytest tests/integration/ -v --tb=short

# Contract tests (validate responses against api.yaml)
pytest tests/contract/ -v --tb=short

# Performance benchmarks
pytest benchmarks/ -v --tb=short

# Full suite with coverage
pytest --cov=app --cov-report=term-missing tests/
```

All tests must pass before the feature is considered implementation-complete.
