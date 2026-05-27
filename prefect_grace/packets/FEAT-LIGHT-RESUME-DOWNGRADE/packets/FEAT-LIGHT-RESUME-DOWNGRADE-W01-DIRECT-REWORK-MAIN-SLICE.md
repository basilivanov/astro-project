# Packet: FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE

## Title
Direct Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE`
- wave_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01`
- packet_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01:packet:FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE`

## Packet Type
rework

## Summary
Address architect-bounded rework for FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE: Fix boundary condition; Update targeted unit expectation; Refresh evidence note

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`

## Review Target
`FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`

## Write Scope
- Only the files required to address architect-bounded blockers from `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`.

## Inputs
- Parent packet `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`.
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
- rework_mode: bounded_fresh

## Reviewer Gate
- All architect-bounded blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE

## Notes
- This is an architect-bounded direct rework packet created after reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-LIGHT-RESUME-DOWNGRADE",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Direct Rework Main Slice",
  "summary": "Address architect-bounded rework for FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE: Fix boundary condition; Update targeted unit expectation; Refresh evidence note",
  "write_scope": [
    "Only the files required to address architect-bounded blockers from `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`."
  ],
  "inputs": [
    "Parent packet `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`.",
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
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "All architect-bounded blocker reasons are addressed.",
    "No new regressions are introduced in the scoped flow."
  ],
  "dependencies": [
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE"
  ],
  "notes": [
    "This is an architect-bounded direct rework packet created after reviewer blockers."
  ],
  "parent_packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE",
  "review_target_packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
