# Packet: FEAT-DYNAMIC-BRIEF-W01-LIVE-IMPLEMENTATION-PACKET

## Summary
Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- FEAT-DYNAMIC-BRIEF-W00-PLANNER-SLICING
- FEAT-DYNAMIC-BRIEF-W00-ARCHITECT-FORMALIZATION
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
-

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-DYNAMIC-BRIEF-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
