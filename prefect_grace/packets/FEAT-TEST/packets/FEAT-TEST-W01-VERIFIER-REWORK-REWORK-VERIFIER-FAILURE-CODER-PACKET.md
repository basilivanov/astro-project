# Packet: FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Title
Verifier Rework Rework Verifier Failure Coder Packet

## GRACE IDs
- feature_ref: `feature:FEAT-TEST`
- wave_ref: `feature:FEAT-TEST:wave:W01`
- packet_ref: `feature:FEAT-TEST:wave:W01:packet:FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET`

## Packet Type
rework

## Summary
Validate the auto-recovery rework for `CODER-1` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`CODER-1`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET
- REVIEWER-1

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit.

## Verification Profile
- backend: rerun minimally sufficient backend checks
- frontend: rerun targeted frontend checks
- observability: repeat post-test digest review

## Execution Hints
- verifier_rework_attempt: 1
- verifier_rework_max_attempts: 3

## Reviewer Gate
- Evidence must correspond to the rework packet.

## Dependencies
- FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Notes
- Auto-created verifier for auto-recovery.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-TEST-W01-VERIFIER-REWORK-REWORK-VERIFIER-FAILURE-CODER-PACKET",
  "feature_id": "FEAT-TEST",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Rework Verifier Failure Coder Packet",
  "summary": "Validate the auto-recovery rework for `CODER-1` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET",
    "REVIEWER-1"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit."
  ],
  "verification_profile": {
    "backend": "rerun minimally sufficient backend checks",
    "frontend": "rerun targeted frontend checks",
    "observability": "repeat post-test digest review"
  },
  "execution_hints": {
    "verifier_rework_attempt": 1,
    "verifier_rework_max_attempts": 3
  },
  "reviewer_gate": [
    "Evidence must correspond to the rework packet."
  ],
  "dependencies": [
    "FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET"
  ],
  "notes": [
    "Auto-created verifier for auto-recovery."
  ],
  "parent_packet_id": "CODER-1",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
