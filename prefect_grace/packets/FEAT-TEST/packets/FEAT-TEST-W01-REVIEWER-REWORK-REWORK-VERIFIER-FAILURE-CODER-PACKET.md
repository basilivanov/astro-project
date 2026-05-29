# Packet: FEAT-TEST-W01-REVIEWER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Title
Reviewer Rework Rework Verifier Failure Coder Packet

## GRACE IDs
- feature_ref: `feature:FEAT-TEST`
- wave_ref: `feature:FEAT-TEST:wave:W01`
- packet_ref: `feature:FEAT-TEST:wave:W01:packet:FEAT-TEST-W01-REVIEWER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET`

## Packet Type
gate_decision

## Summary
Review whether the auto-recovery rework for `CODER-1` addressed the verifier failures.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`CODER-1`

## Review Target
-

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET
- FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Acceptance Criteria
- Exactly one verdict is returned.
- The original failures are resolved.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

## Execution Hints
-

## Reviewer Gate
- Assess only the failed scope.

## Dependencies
- FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET
- FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Notes
- Auto-created reviewer for auto-recovery.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-TEST-W01-REVIEWER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET",
  "feature_id": "FEAT-TEST",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Rework Verifier Failure Coder Packet",
  "summary": "Review whether the auto-recovery rework for `CODER-1` addressed the verifier failures.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET",
    "FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original failures are resolved."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "Assess only the failed scope."
  ],
  "dependencies": [
    "FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET",
    "FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET"
  ],
  "notes": [
    "Auto-created reviewer for auto-recovery."
  ],
  "parent_packet_id": "CODER-1",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
