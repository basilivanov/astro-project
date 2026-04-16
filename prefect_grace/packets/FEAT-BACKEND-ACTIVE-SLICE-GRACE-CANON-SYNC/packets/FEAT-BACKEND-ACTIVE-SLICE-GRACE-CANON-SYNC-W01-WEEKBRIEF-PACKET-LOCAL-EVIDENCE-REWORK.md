# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK`

## Summary
Issue a bounded coder rework for the WeekBrief packet so W01 closes against packet-local read-only evidence instead of claiming canonical today-week observability. Keep the work inside week_brief_service and WeekBrief tests, preserve WeekBrief payload and envelope semantics, and add only the minimal WeekBrief-local attribution needed for readable module/function/block evidence under the W01 packet_local lane.

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

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/requirements.slice.backend-active-slice-grace-canon-sync.xml
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md
- Reviewer blocker: today-week post-test review returned FAIL_NO_EVIDENCE even though W01 owns only packet-local evidence.

## Acceptance Criteria
- Diff stays inside the declared WeekBrief write scope.
- WeekBrief payload, envelope, and API semantics remain unchanged.
- WeekBrief module/function/block attribution remains readable in code and emitted evidence.
- W01 rerun uses packet-local evidence ownership only: targeted WeekBrief tests, backend quick, and `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`.
- The rework does not claim or require canonical today-week closeout; that remains deferred to W02.

## Verification Profile
- backend: Rerun `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
- frontend: Not required; frontend remains frozen and untouched.
- observability: Use packet-local review only: `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`. Report readable WeekBrief-local attribution or an explicit packet-local gap without claiming W02 canonical closeout.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if the rework touches files outside the WeekBrief packet write scope.
- Reject if WeekBrief payload or envelope semantics change.
- Reject if the packet still uses or claims `today-week` canonical closeout in W01.
- Reject if module/function/block evidence remains unreadable and the gap is not explicitly documented.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS

## Notes
- No planner is required; packet topology and wave ownership stay unchanged.
- No user decision is required; this is an execution-lane correction inside existing architect canon.
- Use a fresh bounded coder packet rather than light resume because this source packet family already has rework artifacts and should rerun with a clean acceptance target.
