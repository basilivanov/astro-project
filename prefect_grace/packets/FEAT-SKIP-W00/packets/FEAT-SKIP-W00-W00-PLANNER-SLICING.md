# Packet: FEAT-SKIP-W00-W00-PLANNER-SLICING

## Title
Planner Slicing

## GRACE IDs
- feature_ref: `feature:FEAT-SKIP-W00`
- wave_ref: `feature:FEAT-SKIP-W00:wave:W00`
- packet_ref: `feature:FEAT-SKIP-W00:wave:W00:packet:FEAT-SKIP-W00-W00-PLANNER-SLICING`

## Packet Type
execution

## Summary
Slice the feature into waves and execution packets with explicit dependencies and acceptance gates.

## Wave
W00

## Role
planner

## Reasoning
xhigh

## Parent Packet
-

## Review Target
-

## Write Scope
- Feature-local wave plan.
- Packet definitions for execution waves.

## Inputs
- FEAT-SKIP-W00-W00-ARCHITECT-FORMALIZATION
- Architect manifest and handoff.
- Feature brief `FEAT-SKIP-W00/feature-brief.md`.

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
-

## Reviewer Gate
- No oversized packets.
- No packet without verification expectations.

## Dependencies
- FEAT-SKIP-W00-W00-ARCHITECT-FORMALIZATION

## Notes
- Prefer smaller packets over broad scopes.
- Flag architect escalation when decomposition is ambiguous.
- Return FINAL_GRACE_WAVE_PLAN_JSON markers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-SKIP-W00-W00-PLANNER-SLICING",
  "feature_id": "FEAT-SKIP-W00",
  "wave_id": "W00",
  "packet_type": "execution",
  "role": "planner",
  "reasoning": "xhigh",
  "title": "Planner Slicing",
  "summary": "Slice the feature into waves and execution packets with explicit dependencies and acceptance gates.",
  "write_scope": [
    "Feature-local wave plan.",
    "Packet definitions for execution waves."
  ],
  "inputs": [
    "FEAT-SKIP-W00-W00-ARCHITECT-FORMALIZATION",
    "Architect manifest and handoff.",
    "Feature brief `FEAT-SKIP-W00/feature-brief.md`."
  ],
  "acceptance_criteria": [
    "Every packet has one primary write scope.",
    "Verification and reviewer gates are explicit.",
    "Dependencies allow deterministic execution order.",
    "Planner returns parseable JSON wave contract."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "artifact dependency review"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "No oversized packets.",
    "No packet without verification expectations."
  ],
  "dependencies": [
    "FEAT-SKIP-W00-W00-ARCHITECT-FORMALIZATION"
  ],
  "notes": [
    "Prefer smaller packets over broad scopes.",
    "Flag architect escalation when decomposition is ambiguous.",
    "Return FINAL_GRACE_WAVE_PLAN_JSON markers."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
