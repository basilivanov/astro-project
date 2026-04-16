# Packet-Local Evidence: FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## Scope
- Packet role: `coder`
- Review target: `FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET`
- Evidence window anchored to rerun completed on `2026-04-16T21:29:20+03:00`

## Command Results
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
  - `PASS`
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py`
  - `PASS`
  - `66 passed`
- `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`
  - `PASS_CLEAN`
- `docker exec astro-project-backend-1 sh -lc 'python3 - <<\"PY\" ... PY'`
  - `PASS`
  - Used for fresh packet-local inspection of `/app/logs/feed.jsonl`, `/app/logs/report.jsonl`, and `/app/logs/scheduler.jsonl`

## Evidence Reviewed
- Host read-only review:
  - `/opt/astro-project/logs/feed.jsonl`
  - `/opt/astro-project/logs/report.jsonl`
- Fresh canonical packet-local logs inside backend container:
  - `/app/logs/feed.jsonl`
  - `/app/logs/report.jsonl`
  - `/app/logs/scheduler.jsonl`

## Fresh Traceable Samples
- DayBrief flow:
  - timestamp: `2026-04-16T18:27:17.818769Z`
  - event: `day_brief.built`
  - module/fn/block: `M-DAY-BRIEF-SERVICE` / `build_day_brief_payload` / `DAY_BRIEF_BUILD`
  - correlation_id: `corr-day-brief-e15cf7d425d544e7987f6960adab489e`
  - trace_id: `trace-day-brief-e15cf7d425d544e7987f6960adab489e`
  - request_id: `req-day-brief-e15cf7d425d544e7987f6960adab489e`
  - correlation_source: `day-brief-test`
- Week/API flow:
  - timestamp: `2026-04-16T18:27:17.946589Z`
  - event: `week_brief.response_returned`
  - module/fn/block: `M-API-GATEWAY` / `get_report_detail` / `API_REPORT_DETAIL_ROUTE`
  - correlation_id: `corr-week-api-0f92267a23304fc5a6dd44c9b2f8d000`
  - trace_id: `trace-week-api-0f92267a23304fc5a6dd44c9b2f8d000`
  - request_id: `req-week-api-0f92267a23304fc5a6dd44c9b2f8d000`
  - report_id: `bfbfd3bf-1880-4dd7-bf56-94562e9ddec6`
  - correlation_source: `week-brief-api-test`
- Scheduler flow:
  - timestamp: `2026-04-16T18:27:18.041134Z`
  - event: `scheduler.sub_expired`
  - module/fn/block: `M-OPS-AUTOMATION` / `check_expired_subscriptions` / `SCHEDULER_SUBSCRIPTION_JOB`
  - correlation_id: `corr-scheduler-9984d69a2efb41b09004d33dc4b7e1a2`
  - trace_id: `trace-scheduler-9984d69a2efb41b09004d33dc4b7e1a2`
  - request_id: `req-scheduler-9984d69a2efb41b09004d33dc4b7e1a2`
  - user_id: `eb8e654a-a51e-434a-beed-d21c9ea9bc49`
  - correlation_source: `scheduler-test`

## Interpretation
- DayBrief, Week/API, and Scheduler exercised paths are now reconstructable by `module`, `fn`, `block`, `event`, `correlation_id`, `trace_id`, and `request_id`.
- `tools/post_test_review.py --profile read-only --since 30m --report-format md` remained green, but in this Docker dev setup its host-side review stayed limited to rendered read-surface evidence under `/opt/astro-project/logs/*.jsonl`; fresh canonical packet-local identifiers were confirmed directly from `/app/logs/*.jsonl` inside `astro-project-backend-1`.
- Analytics path non-emission remains explicit:
  - No fresh analytics persistence markers were emitted by the required W01 backend command profile.
  - Classification: `degraded-but-expected` for analytics non-emission only.

## Packet-Local Observability Verdict
- `degraded-but-expected`
- Rationale:
  - The original `no-evidence-blocker` is resolved for exercised DayBrief, Week/API, and Scheduler flows.
  - Remaining degradation is limited to analytics non-emission because the packet-local command profile did not exercise that path.

## Minimal Fix Applied
- `backend/app/services/day_brief.py`
  - `build_day_brief_telemetry(...)` now preserves ambient `request_id` from correlation context when the caller does not pass one explicitly.
- `tests/test_day_brief.py`
  - Added a packet-local log assertion that verifies fresh `day_brief.built` rows carry `correlation_id`, `trace_id`, and `request_id`.
- `tests/test_billing_scheduler.py`
  - Added a packet-local log assertion that verifies fresh scheduler rows carry `correlation_id`, `trace_id`, and `request_id`.
