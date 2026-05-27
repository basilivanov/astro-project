# Packet: FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION

## Title
Rework Implementation

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION`

## Packet Type
rework

## Summary
Address reviewer blockers from FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Need localized rework

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Review Target
-

## Write Scope
- Only the files required to address blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.

## Inputs
- Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.
- Reviewer blocker notes.

## Acceptance Criteria
- Reviewer blockers are addressed directly.
- No unrelated scope expansion.
- Updated verification evidence is ready for re-review.

## Verification Profile
- backend: rerun the minimally sufficient backend profile if backend code changed
- frontend: rerun targeted Playwright if UI changed
- observability: repeat post-test evidence review for the affected flow

## Execution Hints
- sandbox: danger-full-access

## Reviewer Gate
- All blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-REWORK-HINTS-W01-IMPLEMENTATION

## Notes
- This is a localized rework packet created from reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Rework Implementation",
  "summary": "Address reviewer blockers from FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Need localized rework",
  "write_scope": [
    "Only the files required to address blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`."
  ],
  "inputs": [
    "Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.",
    "Reviewer blocker notes."
  ],
  "acceptance_criteria": [
    "Reviewer blockers are addressed directly.",
    "No unrelated scope expansion.",
    "Updated verification evidence is ready for re-review."
  ],
  "verification_profile": {
    "backend": "rerun the minimally sufficient backend profile if backend code changed",
    "frontend": "rerun targeted Playwright if UI changed",
    "observability": "repeat post-test evidence review for the affected flow"
  },
  "execution_hints": {
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "All blocker reasons are addressed.",
    "No new regressions are introduced in the scoped flow."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W01-IMPLEMENTATION"
  ],
  "notes": [
    "This is a localized rework packet created from reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
