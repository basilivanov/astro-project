# Packet: FEAT-VERIFY-OVERRIDE-W01-VERIFIER

## Title
Verifier

## GRACE IDs
- feature_ref: `feature:FEAT-VERIFY-OVERRIDE`
- wave_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01`
- packet_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01:packet:FEAT-VERIFY-OVERRIDE-W01-VERIFIER`

## Packet Type
execution

## Summary
Verify work

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
-

## Write Scope
-

## Inputs
-

## Acceptance Criteria
-

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
- runner: codex

## Reviewer Gate
-

## Dependencies
- FEAT-VERIFY-OVERRIDE-W01-CODER

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-VERIFY-OVERRIDE-W01-VERIFIER",
  "feature_id": "FEAT-VERIFY-OVERRIDE",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier",
  "summary": "Verify work",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {
    "runner": "codex"
  },
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-VERIFY-OVERRIDE-W01-CODER"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
