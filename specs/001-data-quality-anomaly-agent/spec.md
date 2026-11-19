# Feature Specification: AI Data Quality & Anomaly Detection Agent

**Feature Branch**: `001-data-quality-anomaly-agent`

**Created**: 2026-11-18  
**Last Updated**: 2026-11-19 (Aligned with Constitution v1.3.0)

**Status**: Ready for Planning

**Input**: User description: "Two-tier architecture: Level 1 plain code for missing values, duplicates, impossible numbers, outliers (IQR/MAD), and case/spacing normalization ('mumbai' vs 'Mumbai'); Level 2 LLM for context synthesis, polyglot regex patterns, and MCP-ready actionable resolution. Rule-based validity detector (dates with dayfirst format, impossible dates, phone, email, rating range [1-5], delivery days >= 0, quantity > 0). Split duplicates into three classes (exact duplicates auto-dropped, ID collisions to manual review, repeat customers as 'not an issue'). Non-destructive remediation: no fake imputation for rating, email, or phone; recompute total_amount as quantity * unit_price; flag outliers in a 'needs human review' bucket vs 'auto-fixable'. Calibrated scoring weights (missing 1.0, invalid 1.5, arithmetic 2.0, duplicate 1.0, inconsistent 0.5) with table displayed in app, and ground truth benchmark test verifying N of N detected. AI Agent for CSV cleaning with visual sandbox displaying original vs clean changes for user approval, mandatory executable code generation for all value changes, and adaptive novel error identification that synthesizes new detection scripts and updates existing code for future reuse."

---

## Clarifications

### Session 2026-11-19 (Constitution v1.3.0)
- Q: How should proposed data transformations be reviewed and finalized by users? → A: Interactive Visual Sandbox: An isolated workspace displaying side-by-side, cell-level before/after diffs comparing original CSV against proposed cleaned values. No mutation is finalized without explicit user approval.
- Q: What level of transparency is required for data value changes? → A: Mandatory Executable Code Generation: The AI agent MUST always generate exact, self-contained executable Python/pandas code snippets for every cleaning operation, visible in the UI and exported reports.
- Q: What happens when the CSV contains an anomaly type not covered by pre-existing detection scripts? → A: Adaptive Detection & Self-Evolving Rule Engine: The AI agent identifies and isolates the novel error pattern, synthesizes a new deterministic detection rule and unit tests, and permanently registers/updates the detection codebase for continuous learning on future runs.
- Q: How should dates and contact fields be validated? → A: Explicit Day-First Date Parsing (`dayfirst=True`) catching impossible dates (e.g., `2026-02-30`), and rule-based checks for dummy phones (e.g. `0000000000`), email syntax, rating bounds ($[1.0, 5.0]$), non-negative delivery days, and positive quantities.
- Q: How should duplicates be categorized? → A: Three-Tier Duplicate Classification: (1) Exact duplicates are auto-dropped; (2) ID collisions are routed to manual review; (3) Multi-date repeat orders by the same customer are surfaced as "not an issue" / business as usual.
- Q: How should missing or discrepant values in `total_amount`, `rating`, `email`, and `phone` be remediated? → A: Honest Non-Destructive Remediation: `total_amount` is recalculated exactly as $\text{quantity} \times \text{unit\_price}$; `rating`, `email`, and `phone` are preserved as `null`/empty and flagged for human review.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Upload and Profile a Dataset (Priority: P1)

A data analyst or business operator uploads a CSV file (up to ~10,000–50,000 rows) to the application.
The system validates the file, parses it safely, and immediately presents a column-by-column profile
showing inferred semantic types, value distributions, completeness rates, sample values, and a visual completeness mini-chart.
The operator gains an instant understanding of the shape and health of their dataset without writing code.

**Why this priority**: Without upload and profiling, no downstream anomaly detection or reporting is reachable.

**Independent Test**: Upload a valid CSV and verify that a profile summary card appears for each column with
row counts, missing percentages, type inference, distribution statistics, and mini completeness chart.

**Acceptance Scenarios**:
1. **Given** a valid CSV file of ≤ 10,000 rows, **When** uploaded, **Then** the system accepts the file,
   infers semantic types, and displays distribution profiles with a completeness mini-chart.
2. **Given** a file exceeding row limits or containing invalid formatting, **When** uploaded, **Then** the
   system rejects it with an actionable, plain-language error message.
3. **Given** a CSV with varying encodings (e.g., UTF-8 with BOM) or non-standard delimiters, **When** parsed,
   **Then** the system auto-detects parameters and notes any warnings.

---

### User Story 2 — Tier 1 Deterministic Detection & Rule-Based Validity (Priority: P1)

The system scans the dataset using deterministic baseline algorithms across six comprehensive issue families:
1. **Missing values** and sentinel tokens (`N/A`, `unknown`, `-`).
2. **Rule-Based Field Validity (NON-NEGOTIABLE)**:
   - Dates parsed with explicit day-first semantics (`dayfirst=True`), catching unparseable formats, calendar-impossible dates (e.g. `2026-02-30`), and out-of-range timestamps.
   - Emails validated for syntax structure.
   - Phone numbers validated for international/domestic structure, flagging repeated dummy sequences (e.g. `0000000000`).
   - Rating range enforced within domain boundaries ($1.0 \le \text{rating} \le 5.0$).
   - Delivery days verified as non-negative ($\ge 0$).
   - Quantity verified as strictly positive ($> 0$, flagging $\le 0$).
3. **Three-Tier Relational Deduplication**:
   - Tier A (Exact Duplicates): Identical across all columns $\to$ safe for automatic dropping.
   - Tier B (ID Collisions): Same Primary Key (`order_id`) with conflicting transaction details $\to$ routed to manual review.
   - Tier C (Repeat Customers): Same customer on different dates with distinct primary keys $\to$ surfaced explicitly as "not an issue".
4. **Numeric outliers** via IQR (1.5x) and Modified Z-score (MAD), flagged rather than deleted.
5. **Cross-column arithmetic validation** (`quantity * unit_price == total_amount`) with currency cent tolerance ($\pm 0.01$).
6. **Inconsistent categoricals** via whitespace normalization and RapidFuzz candidate clustering.

**Why this priority**: Deterministic detection provides 100% repeatable, judge-verifiable coverage without model hallucinations, covering all planted anomalies.

**Independent Test**: Run detection against `online_store_orders_sample.csv`; verify that true anomalies across all 6 families are flagged, repeat customers are classified as "not an issue", and ID collisions are preserved for manual review.

**Acceptance Scenarios**:
1. **Given** invalid dates (e.g. `2026-02-30`), dummy phones (`0000000000`), negative quantities, or ratings $>5$, **When** validity detection runs, **Then** exact row indices and violation reasons are reported.
2. **Given** multiple orders with the same customer identity on different dates, **When** deduplication runs, **Then** the system displays them as "not an issue" / business as usual.
3. **Given** identical order IDs with conflicting line items, **When** deduplication runs, **Then** they are routed to manual review.
4. **Given** arithmetic inconsistencies (`quantity * unit_price != total_amount`), **When** detection runs, **Then** they are flagged under the arithmetic conflict family with weight 2.0.

---

### User Story 3 — Tier 2 Cognitive LLM Augmentation & MCP Blueprints (Priority: P2)

For each detected issue, the LLM analyzes structured summaries and distinct token samples (with PII masked) to:
- Explain what the issue means and its business impact in clear, non-technical prose.
- Provide executable pandas remediation snippets.
- Recommend multi-locale / polyglot regex patterns for complex formats (phones, postal codes, regional dates).
- Propose structured MCP action blueprints containing tool name, parameters, risk level, and rollback action.

**Why this priority**: Transforms raw mathematical and statistical outputs into actionable guidance that non-technical operators and integrated agents can execute.

**Independent Test**: Review generated explanations for detected findings: verify non-technical clarity, absence of raw PII, executable pandas code blocks, and seamless fallback to deterministic templates when offline.

**Acceptance Scenarios**:
1. **Given** a detected anomaly, **When** the detail card is viewed, **Then** an executive-ready explanation and pandas code snippet are displayed without statistical jargon.
2. **Given** formatted text inconsistencies (phones, dates, codes), **When** Tier 2 analysis executes, **Then** the LLM recommends flexible, multi-format regex patterns.
3. **Given** that the LLM service is offline or rate-limited, **When** explanations are requested, **Then** deterministic templates load instantly without failure.

---

### User Story 4 — Interactive Visual Sandbox, Always-Code & Dual-Bucket Studio (Priority: P2)

The operator reviews proposed cleaning operations inside an Interactive Visual Sandbox before anything is finalized:
1. **Side-by-Side Visual Diff Sandbox**:
   - Compares the original raw CSV values directly against the proposed cleaned values with cell-level highlighting.
   - Changes are segregated into an **"Auto-Fixable Operations"** bucket (casing normalization, whitespace trim, exact duplicate drops, exact arithmetic recalculations) and a **"Needs Human Review"** bucket (outliers, ID collisions, unverified missing fields).
2. **Always-Generated Executable Code**:
   - For every transformation, the AI agent provides the exact, executable Python/pandas code block that performs the mutation, enabling standalone verification.
3. **Human-in-the-Loop Finalization Gate**:
   - No data mutation is finalized or exported without explicit user approval (single-operation click or verified low-risk batch approval).
   - Atomic LIFO undo stack allows instant rollback of applied changes.
4. **Imputation Integrity Rules**:
   - `total_amount` is recomputed exactly as $\text{quantity} \times \text{unit\_price}$ (never median imputed).
   - `rating`, `email`, and `phone` are preserved as `null`/empty and flagged for human review (never filled with synthetic placeholders).
   - Outliers are flagged for review, never silently deleted.

**Why this priority**: Empowers data practitioners with complete visibility, reversibility, and auditability while preventing silent data corruption or synthetic fabrication.

**Independent Test**: Preview operations in the sandbox, inspect before/after diffs and generated pandas code, approve an auto-fixable operation, verify live score update, and perform undo to restore initial state.

**Acceptance Scenarios**:
1. **Given** proposed cleaning operations, **When** the sandbox loads, **Then** side-by-side before/after cell diffs and corresponding executable pandas code snippets are visible for every operation.
2. **Given** an arithmetic mismatch in `total_amount`, **When** applied, **Then** it is recomputed as $\text{quantity} \times \text{unit\_price}$.
3. **Given** missing values in `rating`, `email`, or `phone`, **When** inspected, **Then** the system preserves them as null and flags them rather than inserting made-up values.
4. **Given** an applied operation, **When** the operator clicks "Undo", **Then** the change reverts to the prior snapshot and restores the previous quality score.

---

### User Story 5 — Calibrated Quality Scoring & Executive Export (Priority: P3)

The system displays the calibrated scoring table directly in the application UI, computes live scores before and after cleaning, and generates certified deliverables:
- Standalone executive HTML report (`report.html`) with documented scoring formula, calibrated weights, generated pandas code, and audit trails.
- Sanitized CSV export with `FormulaGuard` protection escaping `=, +, -, @` characters.

**Why this priority**: Provides the primary deliverable for business stakeholders, compliance audits, and hackathon judging.

**Independent Test**: Download the HTML report and cleaned CSV; confirm presence of executive summaries, calibrated weight table, before/after score metrics, transformation audit log, and neutralized spreadsheet formula prefixes.

**Acceptance Scenarios**:
1. **Given** detected findings, **When** scores are computed, **Then** deductions apply calibrated weights (Missing: 1.0, Invalid: 1.5, Arithmetic: 2.0, Duplicate: 1.0, Inconsistent: 0.5), with the weight table visible in the UI.
2. **Given** completed cleaning, **When** the report is exported, **Then** it presents initial vs cleaned quality scores, audit logs, and executable code snippets.
3. **Given** cells starting with `=`, `+`, `-`, or `@`, **When** exported to CSV, **Then** characters are escaped with `'` to eliminate spreadsheet formula execution risks.

---

### User Story 6 — Adaptive Novel Anomaly Discovery & Self-Evolving Rule Engine (Priority: P2)

When an uploaded CSV contains anomalies, invalid values, or formatting corruptions that are **not** covered by existing built-in detection scripts:
1. **Autonomous Discovery**: The AI agent identifies and characterizes the unscripted anomaly pattern (e.g. an exotic date format, novel sentinel token, or unusual cross-field constraint).
2. **Dynamic Rule & Code Synthesis**: The agent automatically synthesizes a new deterministic detection rule (such as a polyglot regex, validation function, or detector class) along with automated test fixtures.
3. **Continuous Learning & Codebase Update**: The agent registers the newly synthesized rule in the persistent detector registry / detection codebase so it is permanently active for subsequent dataset scans.
4. **Transparent Remediation**: The agent generates the corresponding executable pandas remediation snippet and presents the newly detected issues in the visual sandbox for user approval.

**Why this priority**: Prevents the data quality platform from becoming obsolete when faced with emerging real-world anomaly patterns, transforming the system into an evolving self-healing engine.

**Independent Test**: Provide a dataset containing an unscripted anomaly pattern (e.g. an exotic delimiter or unmapped status code); verify that the agent identifies the novel pattern, generates a new detection rule, adds it to the registry, and verifies 0 false positives on clean rows.

**Acceptance Scenarios**:
1. **Given** a CSV with an unrecognized error pattern, **When** the agent runs adaptive analysis, **Then** it isolates the pattern, generates a deterministic rule, and updates the detector registry.
2. **Given** the synthesized rule, **When** validated against clean rows, **Then** it confirms zero false-positive detections before registration.
3. **Given** future scans of similar datasets, **When** detection runs, **Then** the newly registered rule executes automatically as part of the standard detector pipeline.

---

## Edge Cases

- **Repeat Orders Across Multiple Dates**: Same customer, same address, different date and order ID → Valid customer activity; system displays as "not an issue".
- **Identical Order ID with Conflicting Details**: Same `order_id` with different amounts or items → Flagged as high-severity business key collision, routed to manual review.
- **Ambiguous Date Formats**: `15/01/2024` vs `01/15/2024` → Parsed with explicit `dayfirst=True`, detecting calendar-impossible dates (e.g. `2026-02-30`).
- **Dummy Contact Identifiers**: Repetitive digits like `0000000000` → Flagged by validity detector as invalid phone numbers.
- **Negative & Zero Quantities**: `quantity <= 0` → Flagged as invalid order quantity.
- **Rating Out of Bounds**: `rating = 10` or `rating = 6` → Flagged as invalid rating range ($[1, 5]$).
- **Delivery Days Negative**: `delivery_days = -3` → Flagged as invalid duration.
- **Zero-Variance & Constant Columns**: Handled gracefully; statistical detectors skip to prevent division-by-zero.
- **Novel Anomaly False Positive Risk**: When the AI agent synthesizes a new detector rule, it must be validated against existing clean rows to verify zero false positives before registration.

---

## Requirements *(mandatory)*

### Functional Requirements

**Upload & Ingestion**
- **FR-001**: System MUST accept CSV uploads up to 10,000–50,000 rows with MIME and extension validation.
- **FR-002**: System MUST reject empty files, header-only files, or unparseable inputs with actionable messages.
- **FR-003**: System MUST preserve the original uploaded dataset as immutable throughout the session.

**Column Profiling**
- **FR-004**: System MUST infer semantic types (numeric, categorical, datetime, identifier, text).
- **FR-005**: System MUST compute row counts, null counts, distinct counts, distribution summaries, and render a data completeness mini-chart.

**Tier 1 Deterministic Detection & Rule-Based Validity**
- **FR-006**: System MUST detect missing values, whitespace strings, and configurable sentinel tokens (`N/A`, `unknown`, `-`).
- **FR-007 (Rule-Based Validity Detector)**: System MUST implement a dedicated rule-based validity detector validating:
  - Dates: parsed with explicit day-first format (`dayfirst=True`), detecting unparseable formats, impossible calendar dates (e.g. `2026-02-30`), and out-of-range timestamps.
  - Emails: syntax and domain structure.
  - Phones: format, length, and dummy repetition sequences (e.g. `0000000000`).
  - Ratings: domain range enforcement ($1.0 \le \text{rating} \le 5.0$).
  - Delivery days: non-negative duration ($\text{delivery\_days} \ge 0$).
  - Quantities: positive order amounts ($\text{quantity} > 0$, flagging $\le 0$).
- **FR-008 (Three-Tier Duplicate Classification)**: System MUST categorize duplicate checks into:
  - Exact duplicates (auto-dropped).
  - ID collisions (same primary key, conflicting payloads) routed to manual review.
  - Repeat customers (same entity across different dates) surfaced explicitly as "not an issue".
- **FR-009**: System MUST perform cross-column arithmetic consistency checks (`quantity * unit_price == total_amount`) using an absolute tolerance threshold of ±0.01.
- **FR-010**: System MUST detect numeric outliers using dual-method IQR and Modified Z-Score (MAD), flagging them for review rather than deleting.
- **FR-011**: System MUST cluster categorical spelling and spacing variations using case-folding and RapidFuzz similarity.
- **FR-012**: Tier 1 detection results MUST be 100% deterministic and reproducible across repeated runs.

**Tier 2 Cognitive LLM Augmentation & MCP-Ready Actionability**
- **FR-013**: System MUST generate plain-language explanations translated into business risk and non-technical language.
- **FR-014**: System MUST provide executable pandas remediation code snippets for each finding.
- **FR-015**: System MUST recommend multi-format / polyglot regex patterns targeting international phone numbers, postal codes, and regional date formats.
- **FR-016**: System MUST structure recommended remediations as standard MCP tool blueprints containing `tool_name`, `parameters`, `business_summary`, `risk_level` (`low` | `medium` | `high`), and explicit `rollback_action`.
- **FR-017**: System MUST mask all PII (names, emails, phone numbers) before transmitting prompt context to any external LLM.
- **FR-018**: System MUST provide deterministic fallback explanations when external LLM APIs are unreachable.

**Quality Scoring & Ground Truth**
- **FR-019**: System MUST compute an overall dataset score and individual column scores on a 0–100 scale using calibrated severity weights:
  - Arithmetic Conflict: `2.0`
  - Invalid / Validity Error: `1.5`
  - Missing Value: `1.0`
  - Duplicate Collision: `1.0`
  - Inconsistent Categorical: `0.5`
- **FR-020**: System MUST display the calibrated scoring weight table directly in the UI.
- **FR-021**: System MUST recompute scores in real time when cleaning transformations are applied or undone.
- **FR-022**: System MUST maintain a ground truth automated test verifying detection of **N of N planted issues** in the benchmark dataset (`online_store_orders_sample.csv`).

**Visual Sandbox, Always-Code & Cleaning Studio**
- **FR-023 (Interactive Visual Sandbox)**: System MUST provide an interactive visual sandbox displaying side-by-side and cell-level before/after diffs comparing the original raw CSV against proposed cleaned values.
- **FR-024 (Mandatory Always-Code Generation)**: System MUST always generate exact, self-contained executable Python/pandas code blocks for every proposed or applied cleaning transformation.
- **FR-025 (Honest Remediation)**: System MUST NOT impute `rating`, `email`, or `phone` with synthetic placeholders; missing cells MUST remain null and be flagged.
- **FR-026 (Exact Recalculation)**: System MUST recompute `total_amount` as $\text{quantity} \times \text{unit\_price}$ when resolving arithmetic conflicts (never median imputation).
- **FR-027 (Dual-Bucket Studio)**: System MUST present operations partitioned into an "Auto-Fixable" bucket and a "Needs Human Review" bucket.
- **FR-028 (Human Approval Gate)**: System MUST require explicit user approval (single operation or batch low-risk) before finalizing or exporting any data modifications.
- **FR-029 (Atomic LIFO Rollback)**: System MUST support an instant atomic undo operation to revert the most recent transformation.
- **FR-030 (Formula-Injection Defense)**: System MUST sanitize exported CSVs against formula injection by neutralizing `=`, `+`, `-`, and `@` prefixes.
- **FR-031 (Executive HTML Deliverable)**: System MUST produce an executive-ready HTML report containing scores, scoring weight tables, finding summaries, generated code snippets, and transformation audit trails.

**Adaptive Detection & Self-Evolving Rule Engine**
- **FR-032 (Novel Anomaly Pattern Identification)**: The AI agent MUST identify and isolate novel anomaly or error patterns in the CSV that are not covered by existing built-in detection scripts.
- **FR-033 (Dynamic Rule & Detector Synthesis)**: The AI agent MUST automatically synthesize executable detection logic (regex, rule functions, or detector classes) and automated unit tests for newly discovered anomaly patterns.
- **FR-034 (Safety Verification Check)**: Synthesized rules MUST be validated against clean rows in the active dataset to verify zero false positives prior to registration.
- **FR-035 (Persistent Registry & Codebase Update)**: The AI agent MUST register synthesized rules into a persistent detector registry so they are automatically included in all subsequent detection scans.
- **FR-036 (End-to-End Autonomous Orchestration)**: The AI agent MUST orchestrate discovery, rule synthesis, code generation, diff preview generation, and remediation suggestions under human-in-the-loop governance.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Column profiling complete within 30 seconds for files up to 10,000 rows.
- **SC-002**: 100% detection recall (N of N) on planted missing values, rule-based validity errors, arithmetic conflicts, and exact duplicates on benchmark dataset.
- **SC-003**: 0% false-positive duplicate flags on legitimate same-person repeat orders across different dates.
- **SC-004**: Near-duplicate and categorical inconsistency recall of at least 85% on evaluation datasets.
- **SC-005**: Plain-language explanations available within 10 seconds (or fallback within 2 seconds).
- **SC-006**: Zero raw PII transmitted to external LLM services (100% masked).
- **SC-007**: Quality scores visibly improve upon applying approved cleaning operations.
- **SC-008**: Downloadable HTML report generated within 15 seconds.
- **SC-009**: 100% of proposed cleaning actions in the sandbox display corresponding executable pandas code snippets.
- **SC-010**: When a novel unscripted error is identified, the AI agent synthesizes valid, test-passing detection code and registers it within 30 seconds.
- **SC-011**: Dynamically registered detection rules execute on subsequent dataset scans with 0% false positives on previously clean rows.

---

## Target Use Cases & Explicit Boundaries

### In-Scope Business Use Cases
1. **E-Commerce & Retail Order Auditing**: Order reconciliation, duplicate key vs repeat purchase disambiguation, date/phone/email/rating validity checks, pricing recalculations.
2. **Pre-ETL Data Quality Profiling**: Validating batch vendor CSVs before loading into data warehouses.
3. **Legacy Migration Cleansing**: Harmonizing inconsistent categorical spellings and normalizing customer fields.
4. **Adaptive Self-Healing Data Platforms**: Autonomous ingestion where AI agents discover emerging data corruption types, generate permanent detection code, and provide human-in-the-loop sandbox approval.

### Out-of-Scope Limitations
- **Streaming & Big-Data Scale**: Designed for single-node in-memory batch datasets (up to ~10,000–50,000 rows); not a replacement for distributed engines (Spark/Flink).
- **Autonomous Write-Back**: The system will not automatically overwrite production databases without explicit human approval.
