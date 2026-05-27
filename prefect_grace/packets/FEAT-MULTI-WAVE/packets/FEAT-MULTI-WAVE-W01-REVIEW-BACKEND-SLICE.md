# Packet: FEAT-MULTI-WAVE-W01-REVIEW-BACKEND-SLICE

## Title
Review Backend Slice

## GRACE IDs
- feature_ref: `feature:FEAT-MULTI-WAVE`
- wave_ref: `feature:FEAT-MULTI-WAVE:wave:W01`
- packet_ref: `feature:FEAT-MULTI-WAVE:wave:W01:packet:FEAT-MULTI-WAVE-W01-REVIEW-BACKEND-SLICE`

## Packet Type
gate_decision

## Summary
Review backend slice

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-MULTI-WAVE-W01-BACKEND-SLICE`

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
- FEAT-MULTI-WAVE-W01-BACKEND-SLICE
- FEAT-MULTI-WAVE-W01-VERIFY-BACKEND-SLICE

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-MULTI-WAVE-W01-REVIEW-BACKEND-SLICE",
  "feature_id": "FEAT-MULTI-WAVE",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Review Backend Slice",
  "summary": "Review backend slice",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {},
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-MULTI-WAVE-W01-BACKEND-SLICE",
    "FEAT-MULTI-WAVE-W01-VERIFY-BACKEND-SLICE"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-MULTI-WAVE-W01-BACKEND-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
