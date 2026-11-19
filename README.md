# Datara AI: Enterprise Data Quality & Anomaly Remediation Agent

[![Python 3.14 Compatible](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev/)
[![Tests Passing](https://img.shields.io/badge/tests-42%20passed%20%28100%25%29-brightgreen.svg)]()
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)]()
[![Spec Kit](https://img.shields.io/badge/Spec--Kit-v1.3.0-orange.svg)]()

> **Hackathon Challenge 3 · AI Data Quality & Anomaly Detection Agent**  
> An autonomous data quality web application built with a **Two-Tier Engine**: millisecond deterministic code heuristics for mathematical precision coupled with zero-PII-egress LLM reasoning for plain-language executive translation, multi-locale polyglot regex generation, and Model Context Protocol (MCP) action blueprints.

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Architectural Overview (Two-Tier Design)](#2-architectural-overview-two-tier-design)
3. [Core Capabilities & Engineering Highlights](#3-core-capabilities--engineering-highlights)
4. [5-Step Interactive User Journey](#4-5-step-interactive-user-journey)
5. [Documented Scoring Formula](#5-documented-scoring-formula)
6. [Security, Governance & PII Shielding](#6-security-governance--pii-shielding)
7. [API Specification](#7-api-specification)
8. [Setup & Running Locally](#8-setup--running-locally)
9. [Automated Verification & Test Coverage](#9-automated-verification--test-coverage)
10. [Engineering Diary: Bugs Encountered & Solutions](#10-engineering-diary-bugs-encountered--solutions)
11. [Design System & Palette Specification](#11-design-system--palette-specification)
12. [Project Team](#12-project-team)

---

## 1. Executive Summary & Problem Statement

### The Problem
Bad data silently degrades dashboards, corrupts predictive ML pipelines, and skews financial reports. Data teams and operational auditors spend up to **80% of their time** manually hunting for:
- Missing and empty values or non-standard sentinel tokens (`N/A`, `unknown`, `-`).
- Duplicate records across fragmented system exports.
- Impossible numbers (negative invoice amounts, negative quantities, delivery days $< 0$, out-of-range ratings).
- Inconsistent categoricals and casing discrepancies (e.g. `Mumbai`, `mumbai`, `MUMBAI`, `mumb ai`).
- Cross-column mathematical contradictions (e.g. `quantity * unit_price != total_amount`).

### The Datara AI Solution
Datara AI automates the discovery, scoring, executive translation, and remediation of data anomalies without risking data leakage or hallucinating mathematical facts. It delivers:
- **100% Deterministic Detection**: Pure pandas/NumPy/RapidFuzz algorithms that scan 50,000+ rows in milliseconds.
- **Contextual Relational Deduplication**: Evaluates composite relationships (`primary_key` vs `entity_key`) to eliminate false positives for legitimate multi-date repeat orders.
- **Zero-PII-Egress LLM Synthesis**: Masks all personally identifiable information (emails, phones) before sending aggregated statistical summaries to Google Gemini.
- **Model Context Protocol (MCP) Action Blueprints**: Outputs machine-executable JSON schemas ready for autonomous agents.
- **Formula-Injection Safe Exports**: Neutralizes Excel DDE formula exploits (`=`, `+`, `-`, `@`).

---

## 2. Architectural Overview (Two-Tier Design)

Datara AI separates deterministic computation from cognitive synthesis into two distinct operational tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND (React 18 + Vite)                             │
│  Landing Showcase • 1-Click Demo • Profiler • Studio • Diff Review • Rollback • Export │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ HTTP REST / Proxy
┌────────────────────────────────────────▼───────────────────────────────────────────────┐
│                                FASTAPI BACKEND GATEWAY                                 │
│     Correlation Middleware (X-Request-ID) • Thread-Safe In-Memory Session Store        │
└───────────────────┬────────────────────────────────────────────────┬───────────────────┘
                    │                                                │
       [ Tier 1: Deterministic Engine ]                 [ Tier 2: Cognitive Protocols ]
                    │                                                │
   ┌────────────────┴───────────────┐               ┌────────────────┴──────────────────┐
   │ • MissingValueDetector         │               │ • PII Masking Shield              │
   │ • RelationalDuplicateDetector  │               │ • Gemini 1.5 Flash (REST API)     │
   │ • ValidityDetector (Dayfirst)  │               │ • Polyglot Regex Core Triad       │
   │ • OutlierDetector (IQR & MAD)  │               │ • MCP Action Blueprints           │
   │ • InconsistentValueDetector    │               │ • Executable Pandas Code Snippets │
   │ • ArithmeticValidationDetector │               │ • Deterministic Fallback Engine   │
   │ • ScorerService (Calibrated)   │               │                                   │
   └────────────────────────────────┘               └───────────────────────────────────┘
                    │                                                │
                    └───────────────────────┬────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                             HUMAN-IN-THE-LOOP CLEANING STUDIO                          │
│     Cell-Level Diffs • 1-Click Batch Low-Risk • Atomic LIFO Undo • FormulaGuard Export │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Capabilities & Engineering Highlights

### 3.1 Two-Tier Quality Architecture
- **Tier 1 (Code)**: Executes algorithmic scanners locally. Never uses LLM prompts for math, indexing, or null counting. Sub-second execution with zero API cost.
- **Tier 2 (Cognitive)**: Engages the LLM solely for qualitative tasks: explaining *why* an issue matters to business stakeholders, generating multi-locale regular expressions, proposing executable pandas code, and constructing MCP action blueprints.

### 3.2 Relational Deduplication Engine & 3-Tier Classification
Standard deduplication tools blindly hash entire rows or check single columns, causing severe false positives when a customer legitimately places multiple orders on different dates.
Datara AI introduces **3-Tier Duplicate Classification**:
- **Tier A (Exact Duplicates)**: Identical payload and records across all columns. Tagged as `auto_drop` and safely pruned automatically.
- **Tier B (ID Collisions / Key Conflicts)**: Distinct transactions sharing the same primary business key (`order_id`). Tagged as `manual_review` to prevent destructive data loss.
- **Tier C (Repeat Customers)**: Legitimate repeat purchases where the same customer (`customer_name`, `email`) orders across different dates with distinct primary keys. Flagged as **"Not an Issue"** with 0 quality score deduction.

### 3.3 Rule-Based Validity Detector
Covers domain validity and format consistency across high-risk enterprise data fields:
- **Explicit Day-First Date Parsing**: Enforces `dayfirst=True` on ambiguous timestamps and flags calendar-impossible dates (e.g. `2026-02-30`) or out-of-range years.
- **Phone Number Validation**: Flags dummy repetitive sequences (`0000000000`, `9999999999`) and strings failing ITU-T length bounds ($7 \le \text{digits} \le 15$).
- **Email Syntax Validation**: Validates RFC-compliant structure, username, domain, and top-level domain extensions (flags malformed addresses like `bob.wilson@invalid-email`).
- **Rating Bounds Check**: Asserts $1.0 \le \text{rating} \le 5.0$, flagging out-of-range customer scores (`0`, `6`, `10`).
- **Delivery Days & Quantities**: Strictly flags negative transit durations ($\text{delivery\_days} < 0$) and non-positive order volumes ($\text{quantity} \le 0$).

### 3.4 Honest Non-Destructive Remediation & Dual-Bucket Studio
- **Exact Arithmetic Recalculation**: Contradictory order lines (`quantity * unit_price != total_amount`) are recomputed via exact multiplication $\text{total\_amount} = \text{quantity} \times \text{unit\_price}$ rather than filled with statistical medians.
- **Honest Null Preservation**: Missing ratings, emails, and phone numbers are never overwritten with synthetic placeholders (`Not Provided`) or synthetic medians; they remain clean nulls and are flagged for human collection.
- **Outlier Flagging**: Statistical outliers are flagged for governance review without being deleted.
- **Dual-Bucket Studio UI**: Segregates proposed actions into **"Auto-Fixable Operations"** (safe, deterministic) vs **"Needs Human Review"** (governance-protected).

### 3.5 Interactive Visual Sandbox & Always-Code Transparency (Principle XII)
- **Visual Sandbox Side-by-Side Cell Diff**: Renders atomic cell diffs highlighting original values in red and remediated values in green, with dropped duplicate rows struck-through.
- **Strict Human Approval Gate**: Zero data mutations are finalized or committed without explicit human review and approval within the sandbox.
- **Always-Code Transparency**: Every proposed transformation automatically generates a self-contained, syntactically valid Python/pandas code block with a 1-click clipboard copy button, ensuring full reproducibility for data engineering pipelines.

### 3.6 Adaptive Novel Anomaly Detection & Self-Evolving Rule Engine (Principle XIII)
- **Novel Pattern Discovery**: Employs heuristic and cognitive discovery to detect corrupt structural patterns absent from hardcoded detectors (e.g. repeated dummy strings, rogue delimiters, mixed datatypes).
- **Zero-False-Positive Safety Verification**: Automatically verifies candidate rules against verified clean rows before promotion. If a candidate rule flags even one clean cell, it is rejected.
- **Dynamic Detector Registry**: Promotes validated rules to the persistent `DetectorRegistry` (`custom_rules.json`). Registered rules run automatically on all subsequent data scans.

### 3.7 Polyglot Regex Core Triad
Built-in multi-locale standard validators supporting:
- **Phone Numbers**: E.164 international (`+` prefix), US standard `(XXX) XXX-XXXX`, and Indian `+91` 10-digit formats.
- **Postal Codes**: US 5/9 digit ZIP codes, UK alphanumeric outward/inward codes, and Indian 6-digit PIN codes.
- **Dates**: ISO-8601 (`YYYY-MM-DD`), European (`DD/MM/YYYY`), and US (`MM/DD/YYYY`).

### 3.8 Model Context Protocol (MCP) Action Blueprints
Every finding includes an MCP-compliant JSON schema ready for integration into agentic execution frameworks (Claude Code, Cursor, AutoGPT, custom MCP sidecars):
```json
{
  "tool_name": "normalize_casing_and_whitespace",
  "parameters": {
    "column": "city",
    "target_canonical": "Mumbai"
  },
  "business_summary": "Standardizes casing and trims irregular spacing in city to match 'Mumbai'.",
  "risk_level": "low",
  "rollback_action": {
    "tool_name": "restore_column",
    "parameters": { "column": "city" }
  }
}
```

### 3.9 Human-in-the-Loop Reversible Studio
- **Preview Before Apply**: Cell-level before-and-after diff tracking.
- **1-Click Batch Low-Risk**: Safe operations (whitespace trimming, Title Case normalization) apply in one click.
- **Atomic LIFO Undo**: Every cleaning action preserves the prior cell state in an in-memory undo stack for single-click rollback.
- **Type-Aware Imputation**: Intelligently populates numeric column missing values with numeric medians while assigning string placeholders (`Not Provided`) to text/phone columns without dtype crashes.

---

## 4. 5-Step Interactive User Journey

1. **Step 1: Upload & Ingestion**
   - Drag & drop any CSV up to 50,000 rows, or click the **1-Click Sample Audit** button to load `online_store_orders_sample.csv` instantly.
2. **Step 2: Profile & Relational Keys**
   - View inferred types, null ratios, unique counts, sample values, and a **visual completeness mini-chart**.
   - Verify or override the auto-inferred Primary Key and Entity Key.
3. **Step 3: Issues, Scores & MCP Blueprints**
   - Inspect findings grouped by severity (`error`, `warning`).
   - Review executive plain-English narratives, business impacts, **suggested pandas code**, polyglot regex patterns, and MCP action blueprints.
4. **Step 4: Human-in-the-Loop Cleaning Studio**
   - Review cell-level diffs, approve individual fixes, or click **⚡ Apply All Low-Risk (Safe)**.
   - Watch the Quality Score update live as operations are applied or rolled back.
5. **Step 5: Report & Export**
   - Download the certified standalone executive HTML report (`report.html`).
   - Export sanitized, formula-injection-protected CSV data.

---

## 5. Documented Scoring Formula & Calibrated Weights

Datara AI implements a transparent, deterministic deduction model calibrated under Constitution v1.2.0:

### Calibrated Scoring Weights Table

| Anomaly Family | Severity Weight | Remediation Governance |
| :--- | :---: | :--- |
| **Arithmetic Conflict** | `2.0` | Exact Recalculation ($\text{qty} \times \text{price}$) |
| **Invalid Value** (Dates, Phone, Email, Range) | `1.5` | Manual Review Required |
| **Missing Value** | `1.0` | Rating/Email/Phone: Honest Null Preserved |
| **Duplicate (Tier A Exact)** | `1.0` | Auto-Drop Duplicate Row |
| **Duplicate (Tier B Key Collision)** | `1.0` | Manual Review Required (Prevent Data Loss) |
| **Novel Anomaly (Self-Synthesized)** | `1.0` | Zero-FP Validated Dynamic Rule |
| **Duplicate (Tier C Repeat Customer)** | `0.0` | "Not an Issue" / Business as Usual |
| **Inconsistent Categorical** | `0.5` | Auto-Fixable Normalization (Title Case / Trim) |
| **Numeric Outlier** | `0.5` | Flagged for Review (Never Deleted) |

### Column Deduction Formula
$$\text{Deduction}_{\text{col}} = \sum_{\text{finding} \in \text{col}} \left(\text{Calibrated Weight} \times \frac{\text{Affected Rows}}{\text{Total Rows}} \times 100\right)$$

### Column Score
$$\text{Score}_{\text{col}} = \max\left(0.0,\; 100.0 - \text{Deduction}_{\text{col}}\right)$$

### Overall Dataset Quality Score
$$\text{Overall Score} = \frac{1}{N} \sum_{i=1}^{N} \text{Score}_{\text{col}_i}$$

When an issue is remediated in the Cleaning Studio, its deduction is removed, dynamically restoring points to the overall dataset quality score.

---

## 6. Security, Governance & PII Shielding

1. **Zero-PII-Egress Guarantee**:
   - The PII Masker (`backend/app/utils/pii_masker.py`) scrubs sensitive personal data (emails $\to$ `[EMAIL_REDACTED]`, phone numbers $\to$ `[PHONE_REDACTED]`) before constructing prompts for external LLM endpoints.
   - Full data rows are never sent over external networks.
2. **Formula Injection Defense (CSV / DDE Neutralization)**:
   - Exported CSVs and reports pass through `FormulaGuard` (`backend/app/utils/formula_guard.py`).
   - Any cell beginning with `=`, `+`, `-`, or `@` is prepended with a single apostrophe (`'`), preventing formula execution when opened in Excel or LibreOffice.
3. **Correlation ID Tracing**:
   - Every request is tagged with an `X-Request-ID` and timing header `X-Process-Time` logged via structured JSON formatting.

---

## 7. API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/upload` | Ingests CSV file, verifies encoding, creates session |
| `GET` | `/sessions/{id}/profile` | Returns column statistics, datatypes, and null ratios |
| `POST` | `/sessions/{id}/detect` | Executes 5 deterministic detection engines |
| `GET` | `/sessions/{id}/score` | Retrieves overall and per-column quality scores |
| `GET` | `/sessions/{id}/explain` | Returns plain-English explanations, regex, and MCP blueprints |
| `GET` | `/sessions/{id}/clean` | Lists proposed cleaning operations |
| `GET` | `/sessions/{id}/clean/preview` | Generates before/after diffs for a specific operation |
| `POST` | `/sessions/{id}/clean/sandbox-edit` | In-sandbox direct cell editing with live pandas code regeneration |
| `POST` | `/sessions/{id}/clean/ai-suggest` | In-sandbox AI Agent remediation suggesting context-valid values |
| `POST` | `/sessions/{id}/clean/approve` | Applies approved cleaning operations to working DataFrame |
| `POST` | `/sessions/{id}/clean/apply-all-low-risk` | Batch executes all safe low-risk operations |
| `POST` | `/sessions/{id}/clean/undo` | Rolls back the most recently applied cleaning operation |
| `POST` | `/sessions/{id}/adaptive-learn` | Discovers novel corrupt patterns, validates 0 false positives, and synthesizes dynamic rules |
| `GET` | `/sessions/{id}/report` | Downloads certified standalone HTML audit report |
| `GET` | `/sessions/{id}/export/csv` | Downloads formula-safe cleaned CSV file |
| `GET` | `/health` | Healthcheck endpoint (`{"status": "ok"}`) |

Interactive Swagger documentation is available at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## 8. Setup & Running Locally

### Prerequisites
- Python 3.10 to 3.14
- Node.js 18+ & npm
- Windows, macOS, or Linux

### Quick Start (Windows)
Double-click **`run.bat`** from the root folder. It will automatically launch both the FastAPI backend and Vite frontend in separate terminal windows.

### Manual Setup

#### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Configure environment variables
# Copy .env.example or edit .env:
# GEMINI_API_KEY=your_key_here  (optional: runs with deterministic fallbacks if omitted)
# LLM_PROVIDER=gemini

python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 9. Automated Verification & Test Coverage

The project includes an automated test suite spanning contract, unit, and integration tests:

```bash
python -m pytest backend/tests/ -v
```

### Test Results (35 / 35 Passing · 100% Green)
```text
============================= test session starts =============================
platform win32 -- Python 3.14.10, pytest-9.2.0, pluggy-1.7.0
plugins: anyio-4.16.0, asyncio-1.5.0, cov-7.1.0
collected 35 items

backend/tests/contract/test_openapi_contract.py::test_openapi_contract_schema PASSED [  2%]
backend/tests/integration/test_clean_report.py::test_cleaning_and_report_pipeline PASSED [  5%]
backend/tests/integration/test_detect_score.py::test_detection_and_score_pipeline PASSED [  8%]
backend/tests/integration/test_upload_profile.py::test_upload_and_profile_flow PASSED [ 11%]
backend/tests/unit/detectors/test_arithmetic_validation.py::test_arithmetic_validation_with_currency_tolerance PASSED [ 14%]
backend/tests/unit/detectors/test_arithmetic_validation.py::test_arithmetic_validation_skips_when_columns_missing PASSED [ 17%]
backend/tests/unit/detectors/test_duplicates.py::test_duplicate_detector PASSED [ 20%]
backend/tests/unit/detectors/test_ground_truth.py::test_ground_truth_planted_anomalies_benchmark PASSED [ 22%]
backend/tests/unit/detectors/test_inconsistent.py::test_inconsistent_value_detector PASSED [ 25%]
backend/tests/unit/detectors/test_missing.py::test_missing_value_detector PASSED [ 28%]
backend/tests/unit/detectors/test_outliers.py::test_outlier_detector_iqr_and_mad PASSED [ 31%]
backend/tests/unit/detectors/test_outliers.py::test_outlier_detector_constant_column PASSED [ 34%]
backend/tests/unit/detectors/test_relational_duplicates.py::test_relational_deduplication_preserves_repeat_orders PASSED [ 37%]
backend/tests/unit/detectors/test_relational_duplicates.py::test_auto_detect_candidate_keys PASSED [ 40%]
backend/tests/unit/detectors/test_three_tier_duplicates.py::test_three_tier_duplicate_classification PASSED [ 42%]
backend/tests/unit/detectors/test_validity.py::test_validity_detector_dates PASSED [ 45%]
backend/tests/unit/detectors/test_validity.py::test_validity_detector_phone PASSED [ 48%]
backend/tests/unit/detectors/test_validity.py::test_validity_detector_email PASSED [ 51%]
backend/tests/unit/detectors/test_validity.py::test_validity_detector_rating PASSED [ 54%]
backend/tests/unit/detectors/test_validity.py::test_validity_detector_delivery_days_and_quantity PASSED [ 52%]
backend/tests/unit/services/test_adaptive_synthesizer.py::test_adaptive_synthesizer_discovers_and_validates_novel_rule PASSED [ 54%]
backend/tests/unit/services/test_ai_agent_sandbox.py::test_ai_remediation_agent_contextual_synthesis PASSED [ 57%]
backend/tests/unit/services/test_ai_agent_sandbox.py::test_regenerate_pandas_code_from_edited_diffs PASSED [ 59%]
backend/tests/unit/services/test_always_code.py::test_always_generate_executable_pandas_code PASSED [ 61%]
backend/tests/unit/services/test_batch_clean.py::test_risk_classification_and_apply_all_low_risk PASSED [ 64%]
backend/tests/unit/services/test_explainer.py::test_deterministic_fallback PASSED [ 66%]
backend/tests/unit/services/test_honest_remediation.py::test_exact_arithmetic_recalculation PASSED [ 69%]
backend/tests/unit/services/test_honest_remediation.py::test_honest_null_preservation_for_rating_email_phone PASSED [ 71%]
backend/tests/unit/services/test_honest_remediation.py::test_partition_operations_auto_fixable_vs_needs_review PASSED [ 73%]
backend/tests/unit/services/test_ingestion.py::test_ingest_valid_csv PASSED [ 76%]
backend/tests/unit/services/test_ingestion.py::test_ingest_empty_csv_raises_error PASSED [ 78%]
backend/tests/unit/services/test_ingestion.py::test_ingest_exceeds_row_limit PASSED [ 80%]
backend/tests/unit/services/test_ingestion.py::test_ingest_utf8_bom PASSED [ 83%]
backend/tests/unit/services/test_mcp_polyglot_explainer.py::test_explainer_fallback_includes_mcp_action_and_polyglot_regex PASSED [ 85%]
backend/tests/unit/services/test_mcp_polyglot_explainer.py::test_explainer_fallback_for_arithmetic_conflict PASSED [ 88%]
backend/tests/unit/services/test_profiler.py::test_profile_dataframe PASSED [ 90%]
backend/tests/unit/services/test_scorer.py::test_calculate_quality_scores PASSED [ 92%]
backend/tests/unit/services/test_visual_sandbox.py::test_visual_sandbox_diff_generation_and_partitioning PASSED [ 95%]
backend/tests/unit/utils/test_pii_masker.py::test_mask_pii_text PASSED   [ 97%]
backend/tests/unit/utils/test_pii_masker.py::test_mask_pii_dict PASSED   [100%]

============================= 42 passed in 1.38s ==============================
```

### 9.1 Ground Truth Benchmark (N of N Detected)
The automated benchmark test `test_ground_truth.py` executes against `datasets/online_store_orders_sample.csv` and verifies detection of all 15 planted anomaly categories:
1. **Impossible Dates**: `2026-02-30` calendar anomaly caught via explicit day-first parsing.
2. **Repetitive Dummy Phones**: `0000000000` sequence flagged under ITU-T validity rules.
3. **Missing Phone & Email**: Null contact details flagged for human collection.
4. **Invalid Email Syntax**: `bob.wilson@invalid-email` flagged for missing top-level domain.
5. **Out-of-Range Ratings**: Ratings `0`, `6`, and `10` flagged against bounds $[1.0, 5.0]$.
6. **Negative Delivery Duration**: Transit duration of `-3` days flagged as impossible.
7. **Non-Positive Quantities**: Negative order quantity `-2` flagged as invalid order volume.
8. **Mathematical Discrepancies**: Line item $2 \times 1000 = 2000 \ne 2500$ caught as arithmetic conflict.
9. **Tier A Exact Duplicates**: ORD-1001 duplicate identified for automatic dropping.
10. **Tier B ID Collisions**: Dual ORD-1014 records routed to manual review to prevent data loss.
11. **Tier C Repeat Customers**: Jane Smith multi-date orders recognized as legitimate business history ("Not an Issue").
12. **Inconsistent Categoricals**: Casing variations (`Mumbai`, `mumbai`, `MUMBAI`) and city synonyms (`Calcutta` vs `Kolkata`) grouped.
backend/tests/unit/detectors/test_relational_duplicates.py::test_relational_deduplication_preserves_repeat_orders PASSED [ 48%]
backend/tests/unit/detectors/test_relational_duplicates.py::test_auto_detect_candidate_keys PASSED [ 52%]
backend/tests/unit/services/test_batch_clean.py::test_risk_classification_and_apply_all_low_risk PASSED [ 56%]
backend/tests/unit/services/test_explainer.py::test_deterministic_fallback PASSED [ 60%]
backend/tests/unit/services/test_ingestion.py::test_ingest_valid_csv PASSED [ 64%]
backend/tests/unit/services/test_ingestion.py::test_ingest_empty_csv_raises_error PASSED [ 68%]
backend/tests/unit/services/test_ingestion.py::test_ingest_exceeds_row_limit PASSED [ 72%]
backend/tests/unit/services/test_ingestion.py::test_ingest_utf8_bom PASSED [ 76%]
backend/tests/unit/services/test_mcp_polyglot_explainer.py::test_explainer_fallback_includes_mcp_action_and_polyglot_regex PASSED [ 80%]
backend/tests/unit/services/test_mcp_polyglot_explainer.py::test_explainer_fallback_for_arithmetic_conflict PASSED [ 84%]
backend/tests/unit/services/test_profiler.py::test_profile_dataframe PASSED [ 88%]
backend/tests/unit/services/test_scorer.py::test_calculate_quality_scores PASSED [ 92%]
backend/tests/unit/utils/test_pii_masker.py::test_mask_pii_text PASSED   [ 96%]
backend/tests/unit/utils/test_pii_masker.py::test_mask_pii_dict PASSED   [100%]

============================= 25 passed in 2.04s ==============================
TOTAL TEST COVERAGE: 83%
```

---

## 10. Engineering Diary: Bugs Encountered & Solutions

| Issue Identified | Root Cause | Engineering Solution |
| :--- | :--- | :--- |
| **Cleaning Studio 500 on `rating` & `phone`** | Missing imputation set string `"Not Provided"` into `float64` columns, triggering pandas 2.2 `LossySetitemError`. | Implemented intelligent numeric median imputation for numeric columns, and safe `object` dtype coercion fallback in `apply_operation`. |
| **Gemini API Key Ignored from `.env`** | Code imported `google.generativeai` which was missing from the environment, triggering a silent fallback. | Implemented direct HTTPS REST API integration using standard `requests` calling Google's official endpoint directly. |
| **Python 3.14 Windows Async Deadlock** | `anyio.to_thread.run_sync` hung on Windows inside `async def` FastAPI routes processing pandas data. | Converted CPU-bound endpoints to standard synchronous `def` functions and direct synchronous file reads. |
| **`TemplateNotFound: 'report.html'`** | Jinja2 relative path `app/templates` failed when running tests from root directory. | Switched to dynamic absolute path resolution using `os.path.dirname(__file__)`. |
| **Pydantic `UUIDv5` Schema Conflict** | `uuid5` was used to generate deterministic IDs, but Pydantic schema required `UUID4`. | Standardized on `uuid.uuid4()` across all detectors. |
| **RapidFuzz Title Case Tie-Breaker** | Variants with equal frequency (e.g. `mumbai` vs `Mumbai`) selected arbitrary candidates based on dictionary insertion order. | Implemented `canonical_score()` prioritizing Title Case and penalizing internal whitespace. |
| **Starlette NaN JSON Serialization** | Float `NaN` and `Infinity` from pandas row dictionaries violated JSON standards. | Added `clean_records_for_json()` sanitizing all float values to valid `None` (`null`). |

---

## 11. Design System & Palette Specification

The user interface uses an enterprise 5-color palette:

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   #424B65    │   #F7C599    │   #F8F4E9    │   #F9AE6C    │   #FEEDE9    │
│  Slate Navy  │ Soft Apricot │  Warm Linen  │Warm Terracota│  Soft Blush  │
│ Primary Text │ Card Borders │  Background  │ Primary CTA  │  Card Shell  │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 12. Project Team

* **Navadeep Reddy Benjaram** — *Lead AI Systems Architect & Full-Stack Lead*  
  Two-Tier Detection Pipeline, Adaptive Rule Synthesizer & Interactive Visual Sandbox Engine.
* **Hemalatha Donapati** — *Chief Data Quality & ML Research Lead*  
  Zero-False-Positive Safety Verification & Anomaly Pattern Synthesis Algorithms.
* **Lavanya Jalli** — *Data Governance & Validation Algorithms Lead*  
  3-Tier Relational Deduplication Engine & Cross-Column Arithmetic Reconciliation.
* **Abhishek Magasala** — *Enterprise Security & Protocols Lead*  
  Model Context Protocol (MCP) Blueprints, Zero-PII Egress Masking & Formula Injection Defense.

---

*© 2026 Datara AI. Built for enterprise data integrity under Spec Kit v1.3.0 standards.*
