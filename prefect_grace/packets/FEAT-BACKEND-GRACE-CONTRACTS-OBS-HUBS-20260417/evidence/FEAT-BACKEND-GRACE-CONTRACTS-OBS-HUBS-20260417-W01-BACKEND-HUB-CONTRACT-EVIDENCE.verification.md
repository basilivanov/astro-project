# Verifier Evidence: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-EVIDENCE`

## Test Verdict
passed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_billing_scheduler.py tests/test_catalog_logging.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- tail -n 40 /opt/astro-project/logs/feed.jsonl
- tail -n 40 /opt/astro-project/logs/report.jsonl
- find /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence -maxdepth 3 -type f -print 2>/dev/null | sort

## Evidence Reviewed
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- trace_id=ed0a8fd1-27f7-45b2-bb47-4f94186d7df7 correlation_id=a3536da8-0950-4b44-814f-c736bab96b06 event=day_brief.response_returned
- trace_id=a508248c-9ba3-48d2-aa91-d65f6708a6be correlation_id=4ba56576-b7de-420d-a3a5-576fb87a87f4 event=week_brief_built

## Blocking Issues
- none
