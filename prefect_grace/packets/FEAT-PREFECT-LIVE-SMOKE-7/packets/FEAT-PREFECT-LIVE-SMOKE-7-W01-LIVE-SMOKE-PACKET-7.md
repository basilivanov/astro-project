# Packet: FEAT-PREFECT-LIVE-SMOKE-7-W01-LIVE-SMOKE-PACKET-7

## Summary
Run the full GRACE flow through the Prefect worker in dry-run mode after artifact key fix.

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
- FEAT-PREFECT-LIVE-SMOKE-7-W00-PLANNER-SLICING
- FEAT-PREFECT-LIVE-SMOKE-7-W00-ARCHITECT-FORMALIZATION

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
- FEAT-PREFECT-LIVE-SMOKE-7-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
