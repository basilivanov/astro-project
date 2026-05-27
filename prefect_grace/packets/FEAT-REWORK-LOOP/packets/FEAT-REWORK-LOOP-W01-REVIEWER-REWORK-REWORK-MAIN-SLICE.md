# Packet: FEAT-REWORK-LOOP-W01-REVIEWER-REWORK-REWORK-MAIN-SLICE

## Title
Reviewer Rework Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-LOOP`
- wave_ref: `feature:FEAT-REWORK-LOOP:wave:W01`
- packet_ref: `feature:FEAT-REWORK-LOOP:wave:W01:packet:FEAT-REWORK-LOOP-W01-REVIEWER-REWORK-REWORK-MAIN-SLICE`

## Packet Type
gate_decision

## Summary
Review whether the localized rework for `FEAT-REWORK-LOOP-W01-MAIN-SLICE` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-REWORK-LOOP-W01-MAIN-SLICE`

## Review Target
`FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE
- FEAT-REWORK-LOOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE

## Acceptance Criteria
- Exactly one verdict is returned.
- The original blockers are either resolved or explicitly remain.
- No unrelated scope expansion is accepted.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

## Execution Hints
-

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE
- FEAT-REWORK-LOOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE

## Notes
- This reviewer packet was auto-created from reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-LOOP-W01-REVIEWER-REWORK-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-REWORK-LOOP",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Rework Main Slice",
  "summary": "Review whether the localized rework for `FEAT-REWORK-LOOP-W01-MAIN-SLICE` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE",
    "FEAT-REWORK-LOOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original blockers are either resolved or explicitly remain.",
    "No unrelated scope expansion is accepted."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE",
    "FEAT-REWORK-LOOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE"
  ],
  "notes": [
    "This reviewer packet was auto-created from reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-LOOP-W01-MAIN-SLICE",
  "review_target_packet_id": "FEAT-REWORK-LOOP-W01-REWORK-MAIN-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
