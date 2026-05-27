# Feature Brief: FEAT-DEMO-VERIFY2

## Business Intent
Validate verifier parse and routing

## Desired Outcome
Demo Verify2

## In Scope
- Formalize the feature into GRACE artifacts.
- Slice the feature into bounded execution packets.
- Prepare implementation, verification, and review flow.

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

## Wave Proposal
1. Architect formalizes the feature and impacted GRACE deltas.
2. Planner slices execution into waves and packets.
3. Coder, verifier, and reviewer execute W01.

## Open Decisions
- Confirm whether the feature needs frontend visual proof.
- Confirm whether the first execution should stay dry-run or use real Codex runs.
