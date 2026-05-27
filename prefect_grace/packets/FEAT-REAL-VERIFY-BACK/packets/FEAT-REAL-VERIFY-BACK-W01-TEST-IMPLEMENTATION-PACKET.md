# Packet: FEAT-REAL-VERIFY-BACK-W01-TEST-IMPLEMENTATION-PACKET

## Summary
Run a bounded end-to-end test feature through architect, planner, coder, verifier, and reviewer packets.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only files listed in the packet write scope.
- Bounded refactor required by the packet.

## Inputs
- FEAT-REAL-VERIFY-BACK-W00-PLANNER-SLICING
- FEAT-REAL-VERIFY-BACK-W00-ARCHITECT-FORMALIZATION

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
- FEAT-REAL-VERIFY-BACK-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
