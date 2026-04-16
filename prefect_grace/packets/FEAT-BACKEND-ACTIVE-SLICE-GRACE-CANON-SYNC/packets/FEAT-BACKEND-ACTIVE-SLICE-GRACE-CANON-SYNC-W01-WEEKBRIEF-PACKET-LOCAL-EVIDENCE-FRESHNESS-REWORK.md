# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Summary
Issue a bounded fresh coder rework for the WeekBrief portion of the W01 backend active-slice canon-sync packet. Preserve WeekBrief behavior while making the W01 packet-local read-only observability artifact clearly attributable to the current verifier run. W01 must stay on packet-local evidence only and must not claim canonical today-week closeout.

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
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC.md

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md
- Reviewer blocker: backend quick and targeted pytest are green, but no fresh packet-local trace_id/request_id/report_id evidence was attributable to the current verifier run.

## Acceptance Criteria
- Diff remains inside the declared write scope.
- WeekBrief payload, envelope, fallback, and API semantics remain unchanged.
- Backend quick and targeted WeekBrief tests remain green.
- Current-run packet-local read-only evidence is attributable to stable WeekBrief module/function/block names and, when emitted by the flow, current trace_id/request_id/report_id markers.
- W01 continues to use packet-local read-only evidence only and does not require or claim canonical today-week closeout.

## Verification Profile
- backend: Run `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
- frontend: Not required; frontend is frozen and untouched.
- observability: Run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` after backend verification. If needed to prove freshness, supplement with `python3 tools/post_test_review.py --profile read-only --since 30m --report-format json`. Record a packet-local verdict and current-run attributable evidence or an explicit bounded packet-local gap.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if WeekBrief business semantics change.
- Reject if the rework widens into canonical today-week ownership or other backend slices.
- Reject if packet-local evidence is still stale or not attributable to the current verifier run.
- Reject if files outside the bounded write scope are modified without architect approval.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC

## Notes
- Planner is not required because packet topology and wave ownership stay unchanged.
- User escalation is not required because the blocker is evidentiary and packet-local, not a business decision.
- Use `bounded_fresh` instead of `light_resume` because the reviewer explicitly classified this as broader than a tiny in-context fix and the source packet already has stale-evidence history.
