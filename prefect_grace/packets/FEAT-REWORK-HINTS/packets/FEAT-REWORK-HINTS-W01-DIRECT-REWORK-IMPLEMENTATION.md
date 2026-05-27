# Packet: FEAT-REWORK-HINTS-W01-DIRECT-REWORK-IMPLEMENTATION

## Title
Direct Rework Implementation

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-DIRECT-REWORK-IMPLEMENTATION`

## Packet Type
rework

## Summary
Address architect-bounded rework for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Need bounded architect-first rework

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Review Target
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Write Scope
- Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.

## Inputs
- Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.
- Reviewer blocker notes.
- Architect direct rework packet.

## Acceptance Criteria
- Architect-bounded blockers are addressed directly.
- No unrelated scope expansion.
- Updated verification evidence is ready for re-review.

## Verification Profile
- backend: rerun the minimally sufficient backend profile if backend code changed
- frontend: rerun targeted Playwright if UI changed
- observability: repeat post-test evidence review for the affected flow

## Execution Hints
- sandbox: danger-full-access
- rework_mode: bounded_fresh

## Reviewer Gate
- All architect-bounded blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-REWORK-HINTS-W01-IMPLEMENTATION

## Notes
- This is an architect-bounded direct rework packet created after reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-DIRECT-REWORK-IMPLEMENTATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Direct Rework Implementation",
  "summary": "Address architect-bounded rework for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Need bounded architect-first rework",
  "write_scope": [
    "Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`."
  ],
  "inputs": [
    "Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.",
    "Reviewer blocker notes.",
    "Architect direct rework packet."
  ],
  "acceptance_criteria": [
    "Architect-bounded blockers are addressed directly.",
    "No unrelated scope expansion.",
    "Updated verification evidence is ready for re-review."
  ],
  "verification_profile": {
    "backend": "rerun the minimally sufficient backend profile if backend code changed",
    "frontend": "rerun targeted Playwright if UI changed",
    "observability": "repeat post-test evidence review for the affected flow"
  },
  "execution_hints": {
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "All architect-bounded blocker reasons are addressed.",
    "No new regressions are introduced in the scoped flow."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W01-IMPLEMENTATION"
  ],
  "notes": [
    "This is an architect-bounded direct rework packet created after reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "review_target_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
