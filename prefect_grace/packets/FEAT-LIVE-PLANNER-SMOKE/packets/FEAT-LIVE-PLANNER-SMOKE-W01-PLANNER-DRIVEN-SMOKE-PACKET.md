# Packet: FEAT-LIVE-PLANNER-SMOKE-W01-PLANNER-DRIVEN-SMOKE-PACKET

## Summary
Use real Codex planner output markers and a bounded smoke implementation.

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
- FEAT-LIVE-PLANNER-SMOKE-W00-PLANNER-SLICING
- FEAT-LIVE-PLANNER-SMOKE-W00-ARCHITECT-FORMALIZATION
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
- workdir: /tmp/prefect_grace_prod_worktree
- sandbox: danger-full-access

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-LIVE-PLANNER-SMOKE-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
