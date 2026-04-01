# Rendered Gate + Pass Matrix implementation plan (provisional)

## Status

This is a provisional planning note based on repository-local sources only.
The requested external artifact `telegram_files/2026-04-01/rendered_gate_pass_matrix_tz.md` is not present in this workspace, so any repo-external requirements must be reconciled before implementation starts.

## Repo-derived baseline

The current repo already has three adjacent layers:

1. `scripts/run_e2e.sh` as the canonical Playwright execution wrapper.
2. `tools/post_test_review.py` as the post-test observability digest layer.
3. `tools/trace_report.py` as the trace/report reconstruction layer for report workflows.

What is missing is a dedicated rendered verification layer that:
- treats rendered assertions as a first-class verification surface rather than an ad hoc E2E detail;
- records a normalized `pass_mode` across tests, traces, artifacts, and summaries;
- connects Playwright evidence, trace evidence, and post-test verdicts into one pass matrix.

## Target architecture

### 1. Rendered verification layer

Introduce a narrow rendered verification layer that sits between Playwright specs and post-test reporting.

Conceptually:
- Playwright/spec helpers produce **rendered check records** for routes/components/flows.
- A rendered verifier normalizes each record into a stable envelope.
- The envelope is written into test artifacts and can be aggregated into post-test digest output.
- Post-test review consumes rendered evidence together with structured logs / trace anchors.

### 2. Canonical rendered evidence envelope

Each rendered check should converge to a stable payload shape like:

- `flow_id`
- `surface` (`today`, `week`, `admin`, `catalog`, `billing`, `report-read`, ...)
- `scenario_id`
- `pass_mode`
- `status` (`pass`, `fail`, `warn`, `blocked`)
- `assertion_class` (`rendered-structure`, `rendered-content`, `fallback-visibility`, `degradation-expected`, `trace-link`)
- `trace_id` / `report_id` / `request_id` when available
- `artifact_refs` (screenshot, trace zip, HTML snapshot, replay summary path)
- `details`
- `recorded_at`

### 3. Pass matrix model

The pass matrix should not replace existing profiles. It should be an orthogonal classification layer attached to runs/artifacts.

Recommended dimensions:
- **execution profile**: existing project profile (`backend:quick`, `frontend:quick`, `frontend:targeted`, `smoke`, `full-regression`)
- **verification surface**: `contract`, `rendered`, `trace`, `digest`, `replay`
- **pass mode**: semantic meaning of a successful/acceptable outcome
- **verdict**: final gate result for the flow

## Pass mode taxonomy

`pass_mode` should become a small controlled vocabulary shared by tests, artifact writers, and digest tooling.

Recommended initial modes:
- `strict` — rendered result matches intended happy-path shape with no visible degradation.
- `expected-degradation` — rendered result is intentionally degraded and the scenario explicitly expects that.
- `fallback-acceptable` — fallback UI/render path is acceptable for this scenario but not equivalent to strict success.
- `observed-only` — non-blocking rendered capture used as evidence, without strong assertion semantics.
- `blocked-no-evidence` — rendered verification could not produce enough evidence to support a pass decision.

Important separation:
- `pass_mode` is **not** the same as final verdict.
- `pass_mode` describes how a scenario is allowed to pass.
- final verdict still resolves to repo vocabulary such as `clean`, `degraded-but-expected`, `unexpected-degradation`, `no-evidence-blocker`.

## How `pass_mode` should live across the stack

### Tests

Primary home:
- Playwright helper layer under `frontend/e2e` or shared test utilities.
- Optional Python-side test helpers for report/read trace checks.

Rules:
- Every rendered-sensitive scenario declares `pass_mode` explicitly or inherits a suite default.
- Helpers should fail closed when a scenario marked `strict` observes fallback/degradation markers.
- Helpers should require explicit reason metadata for `expected-degradation`.

### Trace

`pass_mode` should not rewrite low-level app telemetry immediately.
Instead, wave 1 should attach `pass_mode` at the verification artifact level and only later, if needed, thread it into trace summaries.

Wave-2 trace integration:
- `tools/trace_report.py` can optionally print a `verification_context` section if a neighboring rendered artifact references the same `trace_id` or `report_id`.

### Artifacts

Recommended artifact location:
- `tmp/gate_artifacts/rendered/<run-id>/...`
- or `test-results/rendered/...` for Playwright-adjacent transient outputs.

Artifact set per scenario:
- rendered summary JSON
- optional markdown digest row
- screenshot path(s)
- Playwright trace path when available
- linked trace/report ids

### Reporting

Two reporting layers should consume `pass_mode`:

1. `scripts/run_e2e.sh` adjacent summarization path
   - optional post-run hook emitting a rendered summary index.
2. `tools/post_test_review.py`
   - aggregate rendered records into the final observability digest.
   - show whether the flow passed in `strict` vs `expected-degradation` mode.

## Bounded implementation waves

### Wave 0 — terminology + doc contract

Goal:
- freeze vocabulary before code changes.

Scope:
- define rendered verification layer
- define `pass_mode`
- define artifact envelope
- define final verdict mapping

Safe write scope:
- docs only

Candidate files:
- `docs/TESTING.md`
- `docs/REGRESSION_MAP.md`
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md`
- new doc for rendered gate / pass matrix

### Wave 1 — non-invasive artifact layer

Goal:
- add rendered evidence emission without breaking current E2E contract.

Scope:
- create a small rendered artifact writer/helper
- let selected Playwright scenarios emit rendered verification JSON
- do not change application runtime contracts
- do not require backend telemetry changes

Safe write scope:
- `frontend/e2e/**`
- `frontend/package.json` only if a helper script is needed
- `scripts/run_e2e.sh` only for optional artifact collection/indexing
- new helper under `tools/` or `frontend/e2e/utils/`

Non-goal:
- no change to current app logs required

### Wave 2 — digest integration

Goal:
- make rendered evidence visible in canonical post-test review.

Scope:
- extend `tools/post_test_review.py` to read rendered summaries
- add compact rendered section to markdown/text digest
- map `pass_mode` + evidence state into final review verdicts

Safe write scope:
- `tools/post_test_review.py`
- `tests/test_post_test_review.py`
- new fixture data under `tests/` if needed

### Wave 3 — trace/report linking

Goal:
- connect rendered evidence to trace/report identities.

Scope:
- allow rendered artifacts to carry `trace_id` / `report_id` / `request_id`
- optionally teach `tools/trace_report.py` to surface nearby rendered verification context
- add report/read oriented verification coverage where rendered and trace layers intersect

Safe write scope:
- `tools/trace_report.py`
- `tests/test_trace_report_cli.py`
- selected e2e/spec helper files only

### Wave 4 — pass matrix rollup

Goal:
- expose one stable matrix/report for handoff.

Scope:
- emit a repo-local markdown or JSON matrix summarizing flows by profile/surface/pass_mode/verdict
- keep it additive, generated from existing artifacts

Safe write scope:
- new reporting helper under `scripts/` or `tools/`
- docs that point to the generated matrix location

## Exact write scopes

### Safe, additive, low-risk

- `docs/TESTING.md`
- `docs/REGRESSION_MAP.md`
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md`
- new planning/spec docs under `docs/`
- new helper modules under `tools/`
- new test fixtures under `tests/`
- `tests/test_post_test_review.py`
- `tests/test_trace_report_cli.py`
- selected `frontend/e2e/**` helper/spec files for artifact emission only

### Medium-risk but still bounded

- `scripts/run_e2e.sh` for post-run artifact indexing
- Playwright config/package scripts if artifact paths or reporters need alignment

### Avoid until later wave

- backend runtime logging schema
- backend report-generation business logic
- existing canonical profile commands in a breaking way
- broad refactors across unrelated E2E suites

## Recommended execution order

1. Finalize terminology and pass-mode vocabulary against the missing external TZ.
2. Land docs-only contract for rendered layer + pass matrix.
3. Implement additive rendered artifact writer for a narrow pilot slice.
4. Pilot on one stable surface first: likely `Today` or `Week` read path.
5. Extend `tools/post_test_review.py` to ingest rendered artifacts.
6. Add trace/report linkage where `trace_id`/`report_id` already exists.
7. Only then consider a generated pass matrix summary for broad handoff use.

## Suggested pilot slice

Best first pilot:
- `Today` + `Week`

Why:
- these flows already have mandatory observability review,
- existing docs already define degradation vocabulary,
- current tooling already knows how to classify them,
- this keeps the first rendered layer tightly aligned with existing gates.

## Verification strategy per wave

- Wave 0: docs review only
- Wave 1: targeted `./scripts/run_e2e.sh e2e/<pilot>.spec.ts -g "<case>"`
- Wave 2: targeted Python tests for `tools/post_test_review.py`
- Wave 3: targeted Python tests for `tools/trace_report.py` + pilot E2E rerun
- Wave 4: artifact-generation smoke on existing outputs; avoid full-regression unless the slice expands

## Open blockers to resolve before implementation

- Exact content of the missing external TZ about Rendered Gate + Pass Matrix.
- Whether `pass_mode` names must match an already agreed vocabulary outside the repo.
- Whether pass matrix output must be markdown, JSON, or both.
- Whether rendered artifacts should live under `tmp/gate_artifacts/` or `test-results/` as the canonical home.
- Whether the first-class pilot surface is `Today`, `Week`, or report-read.
