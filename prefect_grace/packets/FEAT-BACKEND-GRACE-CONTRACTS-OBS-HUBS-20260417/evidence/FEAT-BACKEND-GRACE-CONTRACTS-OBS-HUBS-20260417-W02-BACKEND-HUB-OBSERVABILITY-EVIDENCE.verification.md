# Verifier Evidence: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE`

## Test Verdict
failed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py tests/test_post_test_review.py
- docker exec astro-project-backend-1 ls -la /app/tools
- docker exec astro-project-backend-1 test -f /app/tools/post_test_review.py; echo post_test_review_py_exists=$?
- python3 -m pytest -q tests/test_post_test_review.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format json
- ls -l /opt/astro-project/logs/feed.jsonl /opt/astro-project/logs/report.jsonl /opt/astro-project/logs/scheduler.jsonl /opt/astro-project/logs/diagnostic.jsonl
- find /opt/astro-project/test-results/rendered-gate -maxdepth 2 -type f | sort
- find /tmp/astro-project/logs -maxdepth 1 -type f \( -name 'feed.jsonl' -o -name 'report.jsonl' -o -name 'scheduler.jsonl' -o -name 'diagnostic.jsonl' \) | sort

## Evidence Reviewed
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE.md
- /opt/astro-project/tools/post_test_review.py
- /opt/astro-project/tests/test_post_test_review.py
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /opt/astro-project/logs/scheduler.jsonl
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json

## Blocking Issues
- Contracted container pytest bundle fails because tools.post_test_review is not importable inside astro-project-backend-1
- Required verification command did not pass, so the packet cannot receive a passing test verdict
