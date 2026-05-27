# Packet: FEAT-LIVE-PLANNER-SMOKE-W00-PLANNER-SLICING

## Summary
Slice the feature into waves and execution packets with explicit dependencies and acceptance gates.

## Wave
W00

## Role
planner

## Reasoning
xhigh

## Write Scope
- Feature-local wave plan.
- Packet definitions for execution waves.

## Inputs
- FEAT-LIVE-PLANNER-SMOKE-W00-ARCHITECT-FORMALIZATION
- Feature brief `FEAT-LIVE-PLANNER-SMOKE/feature-brief.md`.

## Acceptance Criteria
- Every packet has one primary write scope.
- Verification and reviewer gates are explicit.
- Dependencies allow deterministic execution order.
- Planner returns parseable JSON wave contract.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact dependency review

## Execution Hints
- workdir: /tmp/prefect_grace_prod_worktree
- sandbox: danger-full-access

## Reviewer Gate
- No oversized packets.
- No packet without verification expectations.

## Dependencies
- FEAT-LIVE-PLANNER-SMOKE-W00-ARCHITECT-FORMALIZATION

## Notes
- Prefer smaller packets over broad scopes.
- Flag architect escalation when decomposition is ambiguous.
- Return FINAL_GRACE_WAVE_PLAN_JSON markers.
