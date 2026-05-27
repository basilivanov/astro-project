# Verifier Evidence: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE`

## Test Verdict
passed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "today or week or core"
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- docker exec astro-project-backend-1 sh -lc 'tail -n 80 /app/logs/feed.jsonl | grep "trace-core-today-" || true; tail -n 120 /app/logs/report.jsonl | grep "trace-core-week-" || true'

## Evidence Reviewed
- /app/logs/feed.jsonl
- /app/logs/report.jsonl
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- trace-core-today-159c815b36a3437e9a918a2a762cc4cf
- corr-core-today-159c815b36a3437e9a918a2a762cc4cf
- req-core-today-159c815b36a3437e9a918a2a762cc4cf
- trace-core-week-6affb7a0c8d1411eb4b53a42b88c1542
- corr-core-week-6affb7a0c8d1411eb4b53a42b88c1542
- req-core-week-6affb7a0c8d1411eb4b53a42b88c1542
- report_id:c9e3372d-c0c6-4f31-9a7d-23362bf624af

## Blocking Issues
- none
