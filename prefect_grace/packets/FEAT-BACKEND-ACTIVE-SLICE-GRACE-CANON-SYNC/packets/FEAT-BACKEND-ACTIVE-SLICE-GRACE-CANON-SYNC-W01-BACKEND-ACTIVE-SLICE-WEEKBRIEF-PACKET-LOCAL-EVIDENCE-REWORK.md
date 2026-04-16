# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK`

## Summary
Run a bounded fresh rework pass for the WeekBrief portion of the backend active-slice canon-sync packet. Preserve WeekBrief payload, envelope, and API semantics while producing fresh packet-local, attributable WeekBrief evidence for W01. Do not require or claim canonical today-week closeout in W01.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/tests/test_week_brief_service.py
- /opt/astro-project/tests/test_week_brief_api.py
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS.md

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/evidence/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-EVIDENCE.verification.md
- Reviewer blocker: backend checks passed, canonical Today/Week closeout is not required for W01, but no fresh packet-local WeekBrief observability artifact was attributable to the current verification run.

## Acceptance Criteria
- Diff remains inside the declared write scope.
- WeekBrief payload, envelope, fallback, and API semantics remain unchanged.
- WeekBrief strict-GRACE module/function/block attribution remains readable in code and tests.
- W01 verification produces fresh packet-local WeekBrief evidence attributable to the current run, or records an explicit bounded packet-local evidence gap without claiming canonical today-week closeout.
- Targeted WeekBrief tests and backend quick remain green.

## Verification Profile
- backend: Run `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
- frontend: Not required; frontend is frozen and must not be touched.
- observability: Use packet-local/read-only evidence only, for example `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`. The verdict may be `degraded-but-expected` only if the lack of canonical Today/Week emission is explicitly tied to W01 packet-local ownership.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if the rework changes WeekBrief business semantics.
- Reject if files outside the bounded write scope are modified.
- Reject if W01 still treats `today-week` canonical closeout as required.
- Reject if packet-local evidence is stale, unattributed to the current run, or missing without an explicit bounded evidence-gap explanation.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC

## Notes
- Planner is not required because packet topology does not change.
- User escalation is not required because this is an evidence ownership and packet-local verification correction, not a business decision.
- Use `bounded_fresh` instead of `light_resume` because the blocker spans verifier evidence freshness and packet-local observability instructions, not just a small code edit.
- W02 remains responsible for canonical `today-week` observability closeout.
