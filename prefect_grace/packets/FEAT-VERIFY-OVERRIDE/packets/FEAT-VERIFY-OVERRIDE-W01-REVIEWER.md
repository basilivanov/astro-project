# Packet: FEAT-VERIFY-OVERRIDE-W01-REVIEWER

## Title
Reviewer

## GRACE IDs
- feature_ref: `feature:FEAT-VERIFY-OVERRIDE`
- wave_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01`
- packet_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01:packet:FEAT-VERIFY-OVERRIDE-W01-REVIEWER`

## Packet Type
gate_decision

## Summary
Review work

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-VERIFY-OVERRIDE-W01-CODER`

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
-

## Reviewer Gate
-

## Dependencies
- FEAT-VERIFY-OVERRIDE-W01-CODER
- FEAT-VERIFY-OVERRIDE-W01-VERIFIER

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-VERIFY-OVERRIDE-W01-REVIEWER",
  "feature_id": "FEAT-VERIFY-OVERRIDE",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer",
  "summary": "Review work",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {},
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-VERIFY-OVERRIDE-W01-CODER",
    "FEAT-VERIFY-OVERRIDE-W01-VERIFIER"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-VERIFY-OVERRIDE-W01-CODER",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
