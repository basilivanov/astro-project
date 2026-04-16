# Verifier Evidence: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W02-BACKEND-ACTIVE-CANON-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W02:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W02-BACKEND-ACTIVE-CANON-EVIDENCE`

## Test Verdict
passed

## Observability Verdict
no-evidence-blocker

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- find /opt/astro-project/logs -maxdepth 2 -type f | sort
- find /opt/astro-project/reports -maxdepth 3 -type f | sort
- find /opt/astro-project/artifacts -maxdepth 3 -type f | sort
- find /opt/astro-project/test-results -maxdepth 3 -type f | sort
- wc -l /opt/astro-project/logs/feed.jsonl /opt/astro-project/logs/report.jsonl /opt/astro-project/logs/scheduler.jsonl
- stat -c '%n %y %s bytes' /opt/astro-project/logs/feed.jsonl /opt/astro-project/logs/report.jsonl /opt/astro-project/logs/scheduler.jsonl
- find /opt/astro-project/test-results/rendered-gate -maxdepth 1 -type f | sort
- find /opt/astro-project/backend/logs -maxdepth 3 -type f | sort
- tail -n 5 /opt/astro-project/logs/feed.jsonl
- tail -n 5 /opt/astro-project/logs/report.jsonl
- tail -n 5 /opt/astro-project/logs/scheduler.jsonl
- rg -n "post_test_review|FAIL_NO_EVIDENCE|FLOW-TODAY|FLOW-WEEK|rendered_gate|rendered-gate" tools tests scripts backend/app | head -n 80
- sed -n '1,220p' /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W02-REVIEW-BACKEND-ACTIVE-CANON-SLICE.md
- stat -c '%n %y %s bytes' /opt/astro-project/test-results/grace-report.json /opt/astro-project/test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json /opt/astro-project/test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json /opt/astro-project/artifacts/day_live_canary/2026-04-11T10-33-17-622Z/diagnostics.json

## Evidence Reviewed
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /opt/astro-project/logs/scheduler.jsonl
- /opt/astro-project/test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- /opt/astro-project/test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- /opt/astro-project/artifacts/day_live_canary/2026-04-11T10-33-17-622Z/diagnostics.json
- /opt/astro-project/test-results/grace-report.json

## Blocking Issues
- post_test_review today-week returned FAIL_NO_EVIDENCE / no-evidence-blocker
- No fresh canonical Today or Week records were found in the last 30 minutes
- Rendered summaries were present but explicitly non-canonical and insufficient
- Scheduler and analytics observability evidence was not freshly exercised by the required today-week profile
