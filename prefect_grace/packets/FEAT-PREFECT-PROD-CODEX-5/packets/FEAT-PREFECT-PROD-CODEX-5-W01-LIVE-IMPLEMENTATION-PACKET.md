# Packet: FEAT-PREFECT-PROD-CODEX-5-W01-LIVE-IMPLEMENTATION-PACKET

## Summary
Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.

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
- FEAT-PREFECT-PROD-CODEX-5-W00-PLANNER-SLICING
- FEAT-PREFECT-PROD-CODEX-5-W00-ARCHITECT-FORMALIZATION

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
- FEAT-PREFECT-PROD-CODEX-5-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
