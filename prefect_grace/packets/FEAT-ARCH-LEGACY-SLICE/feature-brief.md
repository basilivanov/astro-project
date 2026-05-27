# Feature Brief: FEAT-ARCH-LEGACY-SLICE

## Business Intent
Materialize legacy slice docs on explicit request.

## Desired Outcome
Legacy slice

## In Scope
- Legacy docs only.

## Out of Scope
- Full production rollout of the feature.
- Unbounded refactors outside the packet scopes.

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
-

## Visual Expectations
-

## Wave Proposal
1. Architect formalizes the feature and impacted GRACE deltas.
2. Planner runs only when decomposition is complex or explicitly requested.
3. Coder, verifier, reviewer, and architect execute W01.

## Open Decisions
- Confirm whether the feature needs frontend visual proof.
- Confirm whether the first execution should stay dry-run or use real Codex runs.
