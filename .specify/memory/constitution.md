<!--
=== SYNC IMPACT REPORT ===
Version change: 1.2.0 → 1.3.0
Bump rationale: MINOR version bump. Added two foundational autonomous agent capabilities requested by the user:
  - Principle XII: Interactive Visual Sandbox & Always-Code Transparency (Mandatory visual sandbox displaying side-by-side original vs clean diffs; explicit user approval before finalization; AI agent must ALWAYS generate exact executable pandas/Python code for every value change).
  - Principle XIII: Adaptive Novel Anomaly Detection & Self-Evolving Rule Engine (AI agent identifies unscripted/novel errors in CSVs, synthesizes new deterministic detection logic & tests, and updates the detection codebase/registry for continuous learning and future reuse).
Added principles:
  - Principle XII: Interactive Visual Sandbox & Always-Code Transparency
  - Principle XIII: Adaptive Novel Anomaly Detection & Self-Evolving Rule Engine
Modified principles:
  - None (All Principles I through XI retained without regression).
Templates requiring updates:
  - specs/001-data-quality-anomaly-agent/spec.md: ⚠ pending follow-up update (/speckit-specify)
  - specs/001-data-quality-anomaly-agent/plan.md: ⚠ pending follow-up update (/speckit-plan)
  - specs/001-data-quality-anomaly-agent/tasks.md: ⚠ pending follow-up update (/speckit-tasks)
Follow-up TODOs:
  - RATIFICATION_DATE: Still marked TODO awaiting formal business sign-off.
=== END SYNC IMPACT REPORT ===
-->

# Anomaly Detection Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD is mandatory and strictly enforced across the entire codebase:

- Tests MUST be written and reviewed before any implementation code is authored.
- The Red-Green-Refactor cycle is the only acceptable delivery loop:
  1. Write a failing test that captures the intended behaviour.
  2. Obtain user/peer acknowledgement that the test correctly expresses requirements.
  3. Implement the minimum code required to make the test pass.
  4. Refactor to remove duplication and improve clarity, keeping all tests green.
- Unit tests MUST cover every public function/method.
- Integration tests MUST cover every service boundary and external I/O path.
- A pull request with zero new or updated tests for changed logic MUST be rejected.

**Rationale:** Anomaly detection logic is statistically complex and operationally critical.
Regressions caused by under-tested model changes or pipeline mutations can silently degrade
detection quality in production. TDD ensures correctness is encoded before code, not
retrofitted after.

### II. Observability-First

Every component MUST be instrumented before it handles production traffic:

- Structured JSON logging is required at all log levels; free-form text logs are prohibited
  in application code.
- Distributed tracing (e.g., OpenTelemetry) MUST propagate trace and span IDs across all
  service calls, including asynchronous message consumers.
- Metrics (latency percentiles, error rates, detection throughput, model drift indicators)
  MUST be exposed on a `/metrics` endpoint (Prometheus format) or equivalent sink.
- Alerting rules for SLA breach MUST exist before a service goes to production.
- Log, trace, and metric schema changes are treated as breaking API changes and MUST follow
  the versioning policy in the Governance section.

**Rationale:** Anomaly detection pipelines fail silently — a model that stops emitting
anomalies looks healthy until someone checks outcomes. Observability is the only reliable
indicator that the system is performing its purpose.

### III. API-Contract-First

The public interface of every service or library MUST be defined before implementation:

- An OpenAPI 3.x specification (or equivalent schema contract for non-HTTP interfaces such
  as Kafka topics or gRPC) MUST be authored and approved before any handler code is written.
- Consumer-driven contract tests MUST be generated from the specification and MUST pass in CI.
- Breaking changes to any published contract MUST increment the MAJOR version and include a
  migration guide.
- Internal APIs shared across modules follow the same contract-first requirement; they are
  not exempt because they are "internal."

**Rationale:** Contracts serve as the executable specification between teams and between
services. Defining them first prevents implementation drift and ensures that downstream
consumers can code against a stable interface from day one.

### IV. Modular Boundaries Enforced

The system MUST be structured as independently deployable, cohesive modules:

- Each module (ingestion, feature extraction, model inference, alerting, API gateway, etc.)
  MUST have a clearly documented responsibility boundary with no cross-module direct imports.
- Inter-module communication MUST occur exclusively through the defined contracts (HTTP APIs,
  message queues, shared schema libraries).
- Shared utilities MUST live in versioned internal libraries; ad-hoc copy-paste of logic
  across modules is prohibited.
- Circular dependencies between modules are prohibited and MUST be detected in CI.
- Each module MUST be independently buildable, testable, and deployable in isolation.

**Rationale:** Anomaly detection workloads have heterogeneous scaling profiles — the
inference layer scales differently from ingestion. Tight module boundaries allow selective
scaling, independent rollout, and fault isolation.

### V. Performance SLAs Enforced

Latency and throughput targets are first-class requirements, not afterthoughts:

- Every new service endpoint or processing stage MUST have an explicitly documented latency
  budget (p50 / p95 / p99) before implementation begins.
- Load and performance tests MUST run in CI for any change touching the critical detection
  path; a regression beyond the documented budget blocks merge.
- Resource quotas (CPU, memory, network) MUST be declared in deployment manifests; services
  without quotas MUST NOT be deployed to staging or production.
- Benchmarking results MUST be stored alongside the codebase (e.g., in `benchmarks/`) so
  regressions are easily traceable across releases.

**Rationale:** Real-time anomaly detection is latency-sensitive by design. SLA violations
mean delayed or missed anomaly signals. Enforcing budgets at development time prevents
incremental performance decay that is costly to reverse at scale.

### VI. Security by Default

Security controls MUST be built in, not bolted on:

- Secrets (API keys, credentials, certificates) MUST NEVER appear in source code, commit
  history, or container images; use a secrets manager or environment injection exclusively.
- All external-facing endpoints MUST require authentication and authorization; unauthenticated
  access is prohibited unless explicitly approved in the security review record.
- Dependencies MUST be scanned for known vulnerabilities (CVEs) in every CI run; builds with
  CRITICAL or HIGH severity findings MUST fail.
- Data containing PII or sensitive signals MUST be encrypted at rest and in transit; data
  classification MUST be documented in the service's design doc.
- Threat modeling MUST be performed for every new external integration before development
  begins.
- CSV/Report export sanitization MUST be applied (FormulaGuard) to neutralize spreadsheet formula
  injection exploits (`=`, `+`, `-`, `@`).

**Rationale:** Anomaly detection systems often ingest raw operational or behavioural data
that may carry sensitive information. A breach or insider threat could expose confidential
signals or allow adversarial manipulation of detection outcomes.

### VII. Two-Tier Anomaly Architecture & Rule-Based Validity

Detection and diagnosis MUST operate under a strict separation of computational tiers:

- **Tier 1 (Deterministic Baseline Engine)**:
  - All detection of missing values, exact duplicates, numeric outliers (IQR / MAD), impossible
    values, string canonicalization, cross-column arithmetic, and rule-based field validity MUST
    be executed using deterministic algorithms and verified regex patterns.
  - Tier 1 MUST be 100% reproducible and operate offline without external model dependencies.
  - **Rule-Based Validity Detector (NON-NEGOTIABLE)**:
    - Dedicated rule-based checks MUST validate:
      1. **Dates**: Parsed with explicit formats and day-first semantics (`dayfirst=True`, as day $> 12$
         is unambiguous in target datasets). Detects unparseable date formats, calendar-impossible dates
         (e.g., `2026-02-30`), and out-of-range timestamps.
      2. **Email**: Syntax validity and domain structure.
      3. **Phone**: International and domestic phone formatting (e.g., flagging invalid repetitions like `0000000000`).
      4. **Rating Range**: Enforces valid domain bounds ($1.0 \le \text{rating} \le 5.0$).
      5. **Delivery Days**: Enforces non-negative duration ($\text{delivery\_days} \ge 0$).
      6. **Quantity**: Enforces positive order amounts ($\text{quantity} > 0$, flagging $\text{quantity} \le 0$).
- **Tier 2 (Cognitive LLM Augmentation & Polyglot Regex)**:
  - Language models MUST NOT independently classify anomalous rows or compute baseline scores.
  - The LLM layer is invoked strictly to augment Tier 1 findings: synthesizing semantic context,
    recommending polyglot regex patterns across varying international formats, and diagnosing
    nuanced semantic inconsistencies.
  - All LLM inputs MUST be masked for PII (names, emails, phones) before prompt dispatch.

**Rationale:** Rule-based validity checks account for roughly half of planted enterprise anomalies.
Coupling deterministic validity with cognitive LLM synthesis provides mathematical guarantees
and auditability for judges and auditors, while avoiding hallucinated anomaly counts.

### VIII. Relational & Contextual Deduplication (3-Tier Classification)

Deduplication MUST evaluate relational entity integrity rather than isolated row hashes,
and MUST categorize duplicate findings into three distinct operational tiers:

- **Tier A: Exact Duplicates (Auto-Fixable)**:
  - Rows identical across all evaluated business columns represent redundant technical clones.
  - These MUST be marked as safe for automatic dropping (`drop_duplicates`).
- **Tier B: Business Key / ID Collisions (Requires Manual Review)**:
  - Records sharing the same Primary Business Key (e.g., `order_id`) but with conflicting transaction
    payloads (different customers, products, prices, or dates).
  - These MUST be routed to a manual review bucket and MUST NOT be automatically deleted, as deleting
    either row risks critical data loss.
- **Tier C: Repeat Customers (Explicitly 'Not an Issue')**:
  - Multiple records sharing an identical customer identity (name, email, phone) with distinct primary keys
    on different dates represent legitimate repeat purchasing behavior.
  - The engine MUST recognize these and explicitly surface them in the UI as "not an issue" / business as usual.

**Rationale:** Naive column-level or full-row deduplication creates critical false positives in
transactional datasets where same-entity repeat actions are standard business behavior, while blind
deletion on key collisions destroys conflicting order records.

### IX. Business Accessibility & MCP-Enabled Actionability

Output and resolution pathways MUST be actionable for non-technical stakeholders:

- Findings, risks, and remediation options MUST be articulated in executive, non-technical terms:
  - Technical error terms (e.g., "MAD > 3.5 z-score deviation") MUST be translated into clear business
    implications (e.g., "Unusually high quantity of 120 units detected compared to usual order sizes of 1-5 units").
- MCP (Model Context Protocol) Integration:
  - Where remediation involves external systems (ERP, CRM, ticketing), resolution actions SHOULD be
    exposed as MCP tool calls or structured JSON action blueprints.
  - Action proposals MUST specify reversible, previewable operations with estimated risk impact.

**Rationale:** Data quality tools fail in organizations when technical jargon alienates operational
decision-makers. Actionable, non-technical reporting bridges detection and enterprise remediation.

### X. Non-Destructive Remediation & Exact Recalculation (Honest Data Quality)

Remediation and cleaning operations MUST adhere to principles of data truthfulness:

- **No Synthetic Imputation for Critical Identifiers & Ratings**:
  - `rating`, `email`, and `phone` MUST NOT be imputed with fabricated values, synthetic medians,
    or placeholder strings (such as "Not Provided" or fake phone numbers).
  - Unresolved missing cells in these columns MUST be preserved as `null`/empty and flagged for human resolution.
    Filling in a made-up value is worse than leaving the cell empty.
- **Exact Arithmetic Recalculation**:
  - `total_amount` MUST NOT be imputed with a median or generic mean.
  - If `total_amount` is missing or in arithmetic conflict, it MUST be recomputed as $\text{quantity} \times \text{unit\_price}$,
    which is mathematically exact.
- **Outlier Flagging vs Deletion**:
  - Outliers MUST be flagged for review, NOT deleted or overwritten automatically.
  - The studio UI MUST present a clear distinction between an **"Auto-Fixable"** bucket (safe casing, trimming,
    exact duplicate drops) and a **"Needs Human Review"** bucket (outliers, ID collisions, unverified missing fields).

**Rationale:** Fabricating values distorts corporate reporting and legal compliance. Exact mathematical
recomputation and honest null preservation uphold data integrity standards.

### XI. Calibrated Transparent Scoring & Ground Truth Verification

Quality scoring MUST be completely calibrated, deterministic, and verifiable:

- **Calibrated Severity Weights**:
  - Scoring deductions MUST apply explicit, documented weights per issue family:
    - **Arithmetic Conflict**: `2.0` (severe financial/reconciliation impact)
    - **Invalid / Validity Error**: `1.5` (broken formats, impossible numbers, dates, ranges)
    - **Missing Value**: `1.0` (unpopulated attributes)
    - **Duplicate Collision / Duplication**: `1.0` (redundancy and key clashes)
    - **Inconsistent Categorical**: `0.5` (spelling and casing variants)
  - The application MUST expose this scoring weight table directly in the UI for complete auditor transparency.
- **Ground Truth Benchmark Verification**:
  - The test suite MUST maintain a deterministic ground truth test based on the benchmark dataset
    (`online_store_orders_sample.csv`).
  - The test MUST verify that the engine detects **N of N planted issues**, enabling verified
    demonstrations of 100% detection coverage during live hackathon evaluation.

**Rationale:** Arbitrary scoring damages tool credibility. Explicit weighting and ground truth testing
guarantee transparent, reproducible, and verifiable quality scoring.

### XII. Interactive Visual Sandbox & Always-Code Transparency (NON-NEGOTIABLE)

The cleaning, transformation, and finalization lifecycle MUST operate inside a transparent, human-approved sandbox environment:

- **Interactive Visual Sandbox**:
  - The system MUST provide an interactive visual sandbox displaying granular, cell-level before-and-after diffs
    comparing the original raw CSV against proposed cleaned values.
  - No transformation or clean CSV export MUST be finalized without explicit user approval (either granular single-operation
    approval or verified low-risk batch approval).
  - The sandbox MUST support full LIFO undo/reversal so that users can revert applied changes at any point.
- **Mandatory Executable Code Generation**:
  - For every cleaning and transformation action, the AI agent MUST generate exact, self-contained, reproducible
    executable code (e.g., pandas/Python code snippets).
  - The generated transformation code MUST be exposed directly in the UI and downloadable reports, allowing data engineers
    and auditors to inspect, copy, or execute the cleaning pipeline independently without proprietary tool lock-in.

**Rationale:** Black-box data modification destroys enterprise trust. An interactive visual sandbox with explicit
before/after diffs, human approval gates, and always-generated executable code ensures data practitioners retain complete
sovereignty, auditability, and control over their enterprise assets.

### XIII. Adaptive Novel Anomaly Detection & Self-Evolving Rule Engine

The AI agent MUST possess autonomous capabilities to identify novel errors and dynamically update its detection codebase for future reuse:

- **Novel Anomaly Identification (Cognitive Zero-Day Detection)**:
  - When encountering anomalies or corrupt patterns in a CSV for which no pre-existing deterministic script or detector
    currently exists (e.g. unfamiliar domain-specific formats, exotic sentinel values, novel relational discrepancies),
    the cognitive AI agent MUST identify, isolate, and characterize the novel error pattern.
- **Dynamic Rule & Detector Synthesis**:
  - Upon isolating a novel error pattern, the AI agent MUST automatically synthesize a concrete, deterministic detection
    rule (e.g., regex pattern, validation function, or detector class) along with corresponding automated unit tests.
- **Continuous Learning & Codebase Self-Update**:
  - The AI agent MUST update the persistent detector registry / detection codebase so the newly synthesized rule is
    permanently registered and automatically invoked in all subsequent runs.
  - The AI agent MUST simultaneously generate the corresponding executable remediation code and present the new findings
    and proposed transformations in the visual sandbox for user review.

**Rationale:** Static detection engines quickly become obsolete as enterprise data formats, schemas, and anomaly patterns
evolve. Empowering AI agents to identify unscripted errors, synthesize verified detection logic, and update the codebase
creates a self-healing, continuously learning data quality system that compounds in capability over time.

---

## Business Scope, Use Cases & Boundary Limitations

### Target Business Use Cases
1. **E-Commerce & Retail Transaction Auditing**:
   - Order validation, pricing reconciliation (`qty * price = total`), tax/discount anomaly detection,
     date/phone/email validity, and customer entity verification across multi-date purchases.
2. **Batch ETL Data Ingestion Pipelines**:
   - Pre-flight data quality profiling before loading vendor CSVs into production data warehouses.
3. **Migration & Integration Sanitization**:
   - Cleansing legacy CRM/ERP exports with inconsistent categorical aliases (e.g., city/state/payment spelling variants).
4. **Adaptive Self-Healing Data Platforms**:
   - Autonomous ingestion where AI agents discover emerging data corruption types, generate permanent detection code,
     and provide human-in-the-loop sandbox approval.

### Explicit Architectural Limitations & Non-Goals
1. **Single-Node In-Memory Scalability Limit**:
   - The current architecture targets batch CSV files of up to ~10,000 to 50,000 rows within memory.
   - It is NOT designed as a streaming real-time event processor (e.g., Apache Flink) or a distributed
     big-data platform (e.g., Apache Spark).
2. **Deterministic Sovereignty & Human-in-the-Loop Gate**:
   - The LLM will never be granted autonomous authority to delete records, mutate master databases,
     or finalize data modifications without user approval in the sandbox.
3. **Data Privacy Bounds**:
   - The system is architected for zero raw PII egress; external LLM calls only receive anonymized tokens
     and statistical summaries.

---

## Quality Gates

All of the following gates MUST pass before any branch can be merged to the main branch:

- **Unit tests**: 100% of changed logic paths covered; overall coverage MUST NOT regress.
- **Contract tests**: All consumer-driven contract tests green.
- **Ground Truth Benchmark**: "N of N" planted issues detected against benchmark dataset test.
- **Adaptive Rule Verification**: Any dynamically synthesized detector rule MUST pass validation asserting zero false positives on clean rows before registration.
- **Always-Code Validation**: Every proposed cleaning operation MUST provide an executable Python/pandas snippet.
- **Performance tests**: No latency budget regression on critical paths.
- **Dependency scan**: No CRITICAL/HIGH CVEs unresolved.
- **Static analysis**: Linter and type-checker pass with zero errors.
- **Secret scan**: No secrets detected in diff.
- **Circular dependency check**: No new circular imports introduced.

---

## Development Workflow

1. **Specification first**: New work starts with a spec or design document, reviewed and
   approved before any code is written.
2. **Contract definition**: API contracts or message schemas are drafted next and checked in
   as artifacts.
3. **Test authoring**: Failing tests are written to validate the specified behaviour.
4. **Implementation**: Code is written to pass the failing tests; no scope creep beyond the
   agreed spec.
5. **Observability instrumentation**: Logging, metrics, and tracing are added before the
   feature is considered complete.
6. **Code review**: At least one peer review is required; security-sensitive changes require
   two reviewers.
7. **Performance validation**: Performance tests confirm no SLA regressions.
8. **Merge**: All quality gates green; PR merged to main.

---

## Governance

This constitution is the highest-authority document in the project. It supersedes all other
practices, style guides, and team conventions where conflicts arise.

**Amendment procedure**:
- Amendments MUST be proposed as a pull request modifying `.specify/memory/constitution.md`.
- Each amendment MUST include a written rationale, an assessment of downstream impact, and a
  migration plan if existing code or processes must change.
- Amendments require approval from at least two maintainers.
- After approval, the `CONSTITUTION_VERSION` MUST be bumped per semantic versioning rules.

**Versioning policy**:
- MAJOR: Backward-incompatible changes — removal or redefinition of an existing principle,
  or removal of an existing quality gate.
- MINOR: Additive changes — new principle, new quality gate, new section, or material
  expansion of guidance.
- PATCH: Clarifications, wording improvements, typo fixes, or non-semantic refinements.

**Version**: 1.3.0 | **Ratified**: TODO(RATIFICATION_DATE): Set by project owner when formally adopted | **Last Amended**: 2026-11-19
