# Verifier Evidence: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE`

## Test Verdict
failed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md

## Evidence Reviewed
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /opt/astro-project/logs/scheduler.jsonl
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- /opt/astro-project/test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- /opt/astro-project/test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- /opt/astro-project/test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json

## Blocking Issues
- Targeted active-slice pytest command failed with 13 failures in tests/test_week_brief_service.py
- week_brief_service is missing log_grace_event and returns empty payload/envelope objects in the failing cases
- Packet-local reviewed artifacts did not show direct attributable M-WEEK-BRIEF-SERVICE, M-SCHEDULER, M-ANALYTICS, or M-API-GATEWAY runtime evidence
