# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-LIVE-IMPLEMENTATION-PACKET

## Title
Live Implementation Packet

## GRACE IDs
- feature_ref: `feature:FEAT-DEV-RUNTIME-INDICATOR`
- wave_ref: `feature:FEAT-DEV-RUNTIME-INDICATOR:wave:W01`
- packet_ref: `feature:FEAT-DEV-RUNTIME-INDICATOR:wave:W01:packet:FEAT-DEV-RUNTIME-INDICATOR-W01-LIVE-IMPLEMENTATION-PACKET`

## Packet Type
execution

## Summary
Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.

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
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION
- feature brief

## Acceptance Criteria
- Requested code change is implemented within scope.
- Targeted tests are added or updated if needed.
- Implementation notes are left for verifier and reviewer.

## Verification Profile
- backend: backend:quick or targeted tests as required by the packet
- frontend: targeted Playwright run if the packet touches UI
- observability: post-test log, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-DEV-RUNTIME-INDICATOR-W01-LIVE-IMPLEMENTATION-PACKET",
  "feature_id": "FEAT-DEV-RUNTIME-INDICATOR",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Live Implementation Packet",
  "summary": "Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.",
  "write_scope": [
    "Only files required by the packet.",
    "Bounded implementation/refactor required by the feature brief."
  ],
  "inputs": [
    "FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING",
    "FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION",
    "feature brief"
  ],
  "acceptance_criteria": [
    "Requested code change is implemented within scope.",
    "Targeted tests are added or updated if needed.",
    "Implementation notes are left for verifier and reviewer."
  ],
  "verification_profile": {
    "backend": "backend:quick or targeted tests as required by the packet",
    "frontend": "targeted Playwright run if the packet touches UI",
    "observability": "post-test log, digest, and trace review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Packet scope respected.",
    "Verification handoff notes included."
  ],
  "dependencies": [
    "FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING"
  ],
  "notes": [
    "Prefer root-cause fixes.",
    "Strengthen logs if the packet touches runtime flow."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
