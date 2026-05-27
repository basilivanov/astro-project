# Feature Brief: FEAT-ARCH-SLICE

## Business Intent
Add a small dev-only diagnostics surface on day screen.

## Desired Outcome
Dev indicator slice

## In Scope
- Dev-only day screen diagnostics toggle.

## Out of Scope
- No prod behavior change.

## Impacted Surfaces
- backend: packet orchestration and state tracking.
- frontend: define visual verification requirements when UI is touched.
- automation: Prefect flows and Codex launcher integration.
- observability: logs, evidence, and reviewer verdict routing.

## Impacted GRACE Artifacts
- requirements.xml: feature scope and invariants if they change.
- technology.xml: runtime or toolchain updates if they change.
- development-plan.xml: execution topology and packet model.
- knowledge-graph.xml: impacted modules and flow links.
- verification-matrix.md: required tests and evidence gates.

## Acceptance Criteria
- Dev chip expands compact diagnostics.
- Prod stays unchanged.

## Visual Expectations
-

## Wave Proposal
1. Architect formalizes the feature and impacted GRACE deltas.
2. Planner runs only when decomposition is complex or explicitly requested.
3. Coder, verifier, reviewer, and architect execute W01.

## Open Decisions
- Confirm whether the feature needs frontend visual proof.
- Confirm whether the first execution should stay dry-run or use real Codex runs.
