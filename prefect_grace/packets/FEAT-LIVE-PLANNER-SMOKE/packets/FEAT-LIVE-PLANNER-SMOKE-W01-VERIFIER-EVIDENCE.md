# Packet: FEAT-LIVE-PLANNER-SMOKE-W01-VERIFIER-EVIDENCE

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-LIVE-PLANNER-SMOKE-W01-PLANNER-DRIVEN-SMOKE-PACKET
- coder packet file

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.
- Frontend visual verdict is explicit when UI is touched.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /tmp/prefect_grace_prod_worktree
- sandbox: danger-full-access
- runner: verifier
- backend_profile: grace_smoke
- observability_profile: grace_smoke
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-LIVE-PLANNER-SMOKE-W01-PLANNER-DRIVEN-SMOKE-PACKET

## Notes
- Fail the packet if evidence is missing.
