# Packet: FEAT-SKIP-W00-W01-MAIN-SLICE

## Title
Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-SKIP-W00`
- wave_ref: `feature:FEAT-SKIP-W00:wave:W01`
- packet_ref: `feature:FEAT-SKIP-W00:wave:W01:packet:FEAT-SKIP-W00-W01-MAIN-SLICE`

## Packet Type
execution

## Summary
Implement slice

## Wave
W01

## Role
coder

## Reasoning
high

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
-

## Reviewer Gate
-

## Dependencies
- FEAT-SKIP-W00-W00-PLANNER-SLICING

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-SKIP-W00-W01-MAIN-SLICE",
  "feature_id": "FEAT-SKIP-W00",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Main Slice",
  "summary": "Implement slice",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {},
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-SKIP-W00-W00-PLANNER-SLICING"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
