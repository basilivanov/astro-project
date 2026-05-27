# Feature Brief: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424

## Business Intent
Refactor the backend so backend Python files stay under 1000 physical lines, oversized functions are split to stay under the 4000-token target, and every backend module touched by the work has explicit GRACE contracts, maps, and semantic blocks without changing product behavior.

## Desired Outcome
Backend refactor to line limits and GRACE contracts

## In Scope
- Audit backend Python modules under backend/app and identify files over 1000 physical lines.
- Refactor oversized backend files into cohesive modules so each resulting backend Python file is at or below 1000 physical lines, excluding generated/cache/venv files.
- Split oversized functions or endpoint bodies so each function stays under the 4000-token target; if exact tokenization is unavailable, use a conservative semantic split and explain the evidence.
- Add or preserve GRACE module contracts, module maps, function contracts, and paired START/END semantic blocks for every backend module touched by the refactor.
- Keep public API behavior, response schemas, auth behavior, billing behavior, scheduler behavior, and persistence semantics unchanged unless an architect gate explicitly blocks and escalates.
- Update or add backend tests only where needed to preserve behavior through extraction.
- Produce verifier evidence showing file length checks, oversized-function checks, targeted backend tests, and post-test observability/log review.

## Out of Scope
- Do not redesign product behavior, pricing, auth semantics, report schemas, or frontend UI.
- Do not perform broad dependency upgrades or infrastructure rewrites.
- Do not rewrite unrelated frontend, Telegram, billing UI, or generated artifacts unless required by backend tests.
- Do not count virtualenv, node_modules, cache, test-results, generated, or migration snapshot files as backend refactor targets.

## Impacted Surfaces
- backend/app
- backend tests
- observability/log-watch evidence only where needed for verification

## Impacted GRACE Artifacts
- docs/prefect_grace/BLUEPRINT.md only if the architect determines the backend GRACE contract pattern itself changes
- docs/prefect_grace/USAGE.md only if verification or operator workflow changes
- verification-matrix.md only if new backend verification gates are introduced
- knowledge-graph.xml only if module ownership or semantic links materially change

## Acceptance Criteria
- No backend/app Python file touched or created by the feature exceeds 1000 physical lines.
- Any backend/app Python file still above 1000 lines is listed by the architect as an explicit blocked/follow-up wave, not silently accepted.
- No newly touched backend function remains obviously above the 4000-token target; large functions are split by stable semantic responsibility.
- Every touched backend module has a GRACE module contract and module map, plus function contracts and semantic START/END blocks on important entrypoints and major phases.
- Existing backend behavior is preserved by targeted tests and review of changed API/service boundaries.
- Verifier records concrete commands and evidence paths for line-count checks, function-size checks, backend tests, and observability review.
- Reviewer rejects green-only evidence and rejects missing/stale GRACE contract evidence.

## Visual Expectations
-

## Wave Proposal
1. W00 architect formalization must inventory oversized backend files/functions and define safe refactor boundaries.
2. Planner must slice the work into bounded waves by backend domain/module cluster; do not force a single giant implementation packet.
3. Each execution wave must include coder, verifier, reviewer, and architect gate packets.
4. Architect may stop after a safe first wave if the remaining work needs another scheduled feature run, but must record explicit follow-up waves.

## Open Decisions
- Architect decides exact wave boundaries and whether main.py must be split first or after service extraction.
- Architect decides the canonical GRACE contract template for backend modules, reusing existing project style.
- Escalate only if the line/function limits conflict with runtime behavior or require product/API semantics to change.
