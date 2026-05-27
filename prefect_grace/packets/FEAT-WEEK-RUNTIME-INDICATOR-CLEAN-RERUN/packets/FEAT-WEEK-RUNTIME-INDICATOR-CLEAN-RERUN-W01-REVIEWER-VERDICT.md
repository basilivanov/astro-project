# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT`

## Summary
Review the coder implementation and verifier evidence for strict scope compliance, behavior correctness, visual quality, and packet-local evidence ownership.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN/**

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE

## Acceptance Criteria
- The coder packet changes stay within the architect allowed write scope.
- Frozen scope is untouched, including backend, Day, WeekBrief, useTelegram internals, and unrelated Week panels.
- The implementation satisfies dev expand, dev collapse, prod inertness, and non-Week inertness.
- Visible diagnostics include only render path, bootstrap result, and current mode.
- Tests and visual evidence match the verification matrix lanes.
- Packet-local read-only observability verdict is clean or degraded-but-expected.
- No canonical Today/Week closeout is claimed by this wave.

## Verification Profile
- backend: Review changed files and reject backend modifications unless architect approval is present.
- frontend: Review implementation, tests, and visual artifacts for the approved Week-only helper behavior and compact UI expectations.
- observability: Review the packet-local read-only verdict and confirm no canonical Today/Week ownership was introduced.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**
    - /opt/astro-project/frontend/test-results/**
    - /opt/astro-project/frontend/playwright-report/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if all acceptance criteria are met with concrete test and artifact evidence.
- Reject if implementation scope widens beyond the architect manifest.
- Reject if visual evidence is missing or does not prove the top area remains clean and not banner-like.
- Reject if packet-local observability evidence is missing, fragmented, unexpected-degradation, or no-evidence-blocker.
- Reject if reviewer cannot map verifier evidence back to the coder packet.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE

## Notes
- Reviewer should route defects back to coder_week_runtime_indicator_disclosure.
- Reviewer should not request canonical Today/Week closeout because the architect wave scope is packet_local.
