# Implementation Plan: AI Data Quality & Anomaly Detection Agent

**Branch**: `001-data-quality-anomaly-agent` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-data-quality-anomaly-agent/spec.md` (Updated for Constitution v1.3.0)

---

## Summary

Build an enterprise-ready, two-tier data quality and anomaly detection web application that scans a batch CSV dataset (up to ~10,000–50,000 rows in memory), profiles every column, detects comprehensive issue families using deterministic code, rule-based validity checks, and relational deduplication, scores dataset health via a transparent formula, provides plain-language cognitive explanations, polyglot regex, and MCP action blueprints via an LLM, enables safe human-in-the-loop cleaning in an interactive visual sandbox with always-generated executable pandas code, and incorporates an adaptive continuous-learning engine that discovers unscripted novel anomalies, synthesizes new detection rules, and updates the persistent codebase.

### Architecture Highlights
- **Tier 1 (Deterministic Core & Rule-Based Validity)**:
  - **Rule-Based Validity Detector**: Explicit day-first date parsing (`dayfirst=True`), impossible dates (e.g. `2026-02-30`), out-of-range dates, email syntax, phone format / dummy repetition (e.g. `0000000000`), rating range ($[1, 5]$), delivery days ($\ge 0$), and positive quantity ($> 0$).
  - **Three-Tier Duplicate Classifier**: Exact duplicates (auto-dropped), ID collisions (manual review to prevent data loss), and repeat customers (surfaced as "not an issue").
  - **Arithmetic Consistency**: Exact equation validation ($|\text{quantity} \times \text{unit\_price} - \text{total\_amount}| \le 0.01$).
  - **Missing Values & Outliers**: Deterministic null/sentinel detection and IQR/MAD outlier flagging (never deleted without review).
  - **Categorical Inconsistencies**: RapidFuzz clustering with Title Case canonical scoring.
- **Tier 2 (Cognitive LLM & Actionable Resolution)**:
  - Plain-language executive translation, executable pandas remediation code snippets, polyglot regex generation for the Core Triad (phones, postal codes, dates), and standard MCP-ready action blueprints with zero raw PII egress.
- **Interactive Visual Sandbox & Always-Code Transparency**:
  - Side-by-side and cell-level before/after diffs comparing original raw CSV with proposed cleaned values.
  - Dual-bucket partitioning: **"Auto-Fixable"** (whitespace, casing, exact duplicate drops, exact arithmetic recalculations) vs **"Needs Human Review"** (outliers, ID collisions, unverified missing fields).
  - Mandatory executable Python/pandas code block generated for every transformation, exportable and visible in the UI.
  - Human approval gate before finalized export, with atomic LIFO undo stack.
  - Exact mathematical recalculation for `total_amount` ($\text{quantity} \times \text{unit\_price}$).
  - Honest missing value preservation: `rating`, `email`, and `phone` are left null/empty and flagged for human review (never imputed with synthetic placeholders).
- **Adaptive Novel Anomaly Discovery & Self-Evolving Rule Engine**:
  - Autonomous zero-day error identification: analyzes unscripted anomaly patterns in CSV files.
  - Dynamic rule synthesis: synthesizes deterministic regex, validation logic, and automated unit test assertions.
  - Zero-false-positive safety verification against clean rows.
  - Persistent detector registry (`backend/app/detectors/registry.py`) dynamically loads and persists synthesized rules across sessions for continuous learning.
- **Calibrated Scoring & Ground Truth Verification**:
  - Calibrated severity weights: Arithmetic (2.0), Invalid (1.5), Missing (1.0), Duplicate (1.0), Inconsistent (0.5), Outlier (0.5), Repeat Customer (0.0), displayed directly in the UI.
  - Automated Ground Truth Test verifying **N of N planted issues** detected on `online_store_orders_sample.csv`.

---

## Technical Context

**Language/Version**: Python 3.11+ (FastAPI backend); Node.js 20 LTS (React + Vite frontend)

**Primary Dependencies**:
- Backend: `fastapi`, `uvicorn[standard]`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `rapidfuzz`, `pydantic` v2, `python-multipart`, `openpyxl`, `email-validator`, `phonenumbers`, `jinja2`, `python-dotenv`, `requests`, `httpx`
- Frontend: `react`, `react-dom`, `vite`, `axios`, `recharts`, `lucide-react`
- Testing: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`

**Storage**: In-memory session store (`SessionStore`) managing immutable original DataFrames, working copies, finding entities, transformation audit logs, and persistent JSON rule registry (`backend/app/detectors/custom_rules.json`).

**Testing**: pytest (unit, integration, contract, and ground truth benchmark tests); TDD mandatory per Principle I.

**Target Platform**: Cross-platform single-node server / local development environment (Windows/Linux/macOS).

**Performance Goals**:
- File upload + profile: ≤ 30 s for 10,000 rows (SC-001)
- Deterministic detection run: ≤ 30 s for 10,000 rows
- LLM explanation batch: ≤ 10 s (fallback ≤ 2 s) (SC-005)
- Adaptive rule synthesis: ≤ 30 s (SC-010)
- Report generation: ≤ 15 s (SC-008)

**Constraints**:
- Single-node batch in-memory processing up to 50,000 rows (streaming distributed big data out of scope)
- Zero raw PII transmitted to external LLM providers (SC-006)
- Deterministic detection reproducibility (FR-012)
- Reversible human-approved cleaning with formula-injection guard on export (FR-023, FR-030)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Evidence / Mitigation |
|---|---|---|
| **I. Test-First** | ✅ PASS | All detectors, relational dedup, arithmetic validation, and cleaning operations follow TDD. Unit tests written and verified before implementation. |
| **II. Observability-First** | ✅ PASS | Structured JSON logging with request correlation IDs; `/health` endpoint exposed. |
| **III. API-Contract-First** | ✅ PASS | OpenAPI 3.1 contract defined in `contracts/api.yaml` and Pydantic v2 schemas in `models/`. |
| **IV. Modular Boundaries** | ✅ PASS | Strict boundaries between `ingestion`, `profiler`, `detectors`, `scorer`, `explainer`, `cleaner`, `reporter`, and `registry`. |
| **V. Performance SLAs** | ✅ PASS | Sub-30s latency budgets documented and validated on 10k rows. |
| **VI. Security by Default** | ✅ PASS | PII masking regex utility; CSV formula injection neutralization; API keys via environment variables only. |
| **VII. Two-Tier Architecture & Rule-Based Validity** | ✅ PASS | Strict separation: Tier 1 pure code finds/scores anomalies; Rule-Based Validity detector covers dates (dayfirst), phone, email, rating [1-5], delivery days, and quantity > 0. |
| **VIII. Relational Deduplication (3-Tier)**| ✅ PASS | Exact duplicates auto-dropped; ID collisions routed to manual review; repeat customers surfaced as 'not an issue'. |
| **IX. Business Accessibility** | ✅ PASS | Findings translated into executive non-technical language with structured, reversible action schemas. |
| **X. Non-Destructive Remediation & Exact Recalculation** | ✅ PASS | No synthetic imputation for rating/email/phone; total_amount recomputed as quantity * price; outliers flagged; dual-bucket studio. |
| **XI. Calibrated Transparent Scoring & Ground Truth** | ✅ PASS | Calibrated weights (Arithmetic: 2.0, Invalid: 1.5, Missing: 1.0, Duplicate: 1.0, Inconsistent: 0.5) displayed in UI; N of N ground truth automated test. |
| **XII. Interactive Visual Sandbox & Always-Code Transparency** | ✅ PASS | Side-by-side cell diff sandbox; mandatory human approval gate; LIFO undo; always-generated executable pandas code. |
| **XIII. Adaptive Novel Anomaly Detection & Self-Evolving Rule Engine** | ✅ PASS | AI agent detects unscripted errors, synthesizes deterministic rules and unit tests, verifies 0 false positives, and updates persistent registry. |

**Gate result**: All 13 constitutional principles PASS.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-data-quality-anomaly-agent/
├── plan.md              # This file
├── research.md          # Research decisions & trade-offs
├── data-model.md        # Entities, schemas, and state transitions
├── quickstart.md        # Step-by-step verification guide
├── contracts/
│   ├── api.yaml         # OpenAPI 3.1 REST contract
│   └── schemas.py       # Pydantic v2 contract models
└── tasks.md             # Actionable task list
```

### Source Code

```text
backend/
├── app/
│   ├── main.py                     # App factory, CORS, correlation logging
│   ├── routers/
│   │   ├── upload.py               # POST /upload
│   │   ├── profile.py              # GET /sessions/{id}/profile
│   │   ├── detect.py               # POST /sessions/{id}/detect
│   │   ├── explain.py              # GET /sessions/{id}/explain
│   │   ├── clean.py                # GET/POST /sessions/{id}/clean (preview, approve, undo)
│   │   ├── score.py                # GET /sessions/{id}/score
│   │   ├── adaptive.py             # POST /sessions/{id}/adaptive-learn (Novel rule synthesis)
│   │   └── report.py               # GET /sessions/{id}/report & /export/csv
│   ├── models/                     # Shared Pydantic v2 domain schemas
│   ├── detectors/
│   │   ├── base.py                 # Abstract detector base with JSON serializer guards
│   │   ├── registry.py             # Persistent detector registry for continuous learning (NEW)
│   │   ├── custom_rules.json       # Persisted dynamically synthesized rules (NEW)
│   │   ├── missing.py              # Missing & sentinel token scanner
│   │   ├── validity.py             # Rule-based field & domain validity detector
│   │   ├── duplicates.py           # 3-tier exact, ID collision & repeat customer detector
│   │   ├── outliers.py             # IQR + MAD + impossible value detector (flag only)
│   │   ├── validation.py           # Arithmetic consistency (qty * price == total)
│   │   └── inconsistent.py         # Normalization + RapidFuzz candidate clustering
│   ├── services/
│   │   ├── ingestion.py            # Encoding/MIME validation & safe reading
│   │   ├── profiler.py             # Type inference & summary statistics
│   │   ├── scorer.py               # Calibrated deduction scoring formula
│   │   ├── explainer.py            # LLM adapter with PII masking, pandas code & regex
│   │   ├── cleaner.py              # Visual sandbox engine, always-code, dual buckets & reversible ops
│   │   ├── synthesizer.py          # Adaptive rule synthesizer & zero-false-positive verifier (NEW)
│   │   └── reporter.py             # Jinja2 executive HTML report & CSV exporter
│   ├── utils/
│   │   ├── session.py              # Thread-safe in-process session manager
│   │   ├── pii_masker.py           # Phone & email sanitization regexes
│   │   └── formula_guard.py        # CSV formula injection prevention
│   └── templates/
│       └── report.html             # Executive-ready HTML report template
frontend/
├── src/
│   ├── pages/App.jsx               # 5-step interactive workflow wizard, visual sandbox & adaptive learning
│   ├── services/api.js             # Axios client with adaptive learn endpoints
│   └── main.jsx
datasets/
└── online_store_orders_sample.csv  # Benchmark dataset with planted anomalies
```

---

## Complexity Tracking

> No constitutional violations. All thirteen principles satisfied by design.
