# Packet: FEAT-LIGHT-RESUME-DOWNGRADE-W01-REVIEW-SLICE

## Title
Review Slice

## GRACE IDs
- feature_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE`
- wave_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01`
- packet_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01:packet:FEAT-LIGHT-RESUME-DOWNGRADE-W01-REVIEW-SLICE`

## Packet Type
gate_decision

## Summary
Review slice

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`

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
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-VERIFY-SLICE

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-REVIEW-SLICE",
  "feature_id": "FEAT-LIGHT-RESUME-DOWNGRADE",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Review Slice",
  "summary": "Review slice",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {},
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE",
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-VERIFY-SLICE"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
