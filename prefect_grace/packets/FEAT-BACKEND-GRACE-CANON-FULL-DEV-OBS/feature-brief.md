# Feature Brief: FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS

## Business Intent
Bring the current backend active slice to strict GRACE addressability and dense development-phase structured observability so multi-agent execution, review, and trace-first verification become reliable before deep backend refactor.

## Desired Outcome
Backend GRACE Canon Sync and Full Dev Observability

## In Scope
- Add or align module contracts and module maps in backend active-slice modules that are still not fully formalized.
- Add function contracts on exported, orchestration, and side-effect entrypoints.
- Add paired START_BLOCK and END_BLOCK anchors for major business phases with stable semantic names.
- Expand structured logging on development-critical paths for function entry and exit, major steps, branching, fallback, retry, external calls, persistence boundaries, exception conversion, and closeout.
- Cover backend/app/main.py, backend/app/logging_utils.py, backend/app/services/day_brief.py, backend/app/services/week_brief_service.py, backend/app/services/scheduler.py, backend/app/services/analytics.py, backend/app/services/day_brief_validators.py, and correlation/logging glue around them.
- Preserve the existing logging core and correlation model and extend disciplined usage of log_grace_event(...) and build_grace_log_payload(...).

## Out of Scope
- Do not change scoring semantics.
- Do not change day, week, or natal business behavior.
- Do not do a frontend pass in this feature.
- Do not deeply decompose report_workflow.py in the same feature.
- Do not turn the feature into a repo-wide cleanup outside the backend active slice.
- Do not invent a new logging format when the current GRACE logging envelope already exists.

## Impacted Surfaces
- backend
- observability
- grace

## Impacted GRACE Artifacts
- requirements.xml
- technology.xml
- development-plan.xml
- knowledge-graph.xml
- verification-matrix.md

## Acceptance Criteria
- Backend active slice is formally addressable by module contracts, module maps, function contracts, and semantic blocks.
- Structured logs exist on development-critical transitions across the targeted backend slice and are attributable by module, function, block, event, correlation_id, and trace_id.
- Backend quick verification remains green via docker exec astro-project-backend-1 python3 scripts/pipeline.py.
- Post-test and log-watch review can reconstruct a coherent scenario history from trace and correlation identifiers without guesswork.
- Reviewer and verifier can reason about ownership boundaries, entrypoints, fallbacks, and closeout directly from GRACE canon plus logs.
- The feature does not change backend business semantics for day, week, natal, scoring, or payload contracts.

## Visual Expectations
-

## Wave Proposal
1. W00 architect + planner formalization against the current backend active slice
2. W01 backend canon sync for contracts, maps, function contracts, and semantic blocks
3. W02 backend development-phase observability coverage across critical paths
4. W03 final verification, review, and architect closeout

## Open Decisions
- Reuse the current backend active slice as the canonical boundary unless code inspection proves a real slice mismatch.
- Keep this backend-only and do not widen into frontend or report_workflow decomposition in the same feature.
- {'Treat local size guardrails as strict local policy': 'file <= 1000 lines, function <= 4000 tokens.'}
