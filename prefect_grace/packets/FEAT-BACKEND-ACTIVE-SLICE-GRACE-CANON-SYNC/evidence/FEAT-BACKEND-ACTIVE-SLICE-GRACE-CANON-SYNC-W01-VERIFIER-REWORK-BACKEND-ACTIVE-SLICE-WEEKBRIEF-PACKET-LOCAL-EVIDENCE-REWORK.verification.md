# Verifier Evidence: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK`

## Test Verdict
passed

## Observability Verdict
clean

## Frontend Visual Verdict
not_applicable

## Commands Run
- sed -n '1,220p' prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK.md
- git status --short
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- rg -n "trace-weekbrief-rework-20260416|corr-weekbrief-rework-20260416|req-weekbrief-rework-20260416|week_brief_packet_scope|week_brief_built" logs artifacts prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC -g '!**/node_modules/**'
- docker exec astro-project-backend-1 sh -lc 'find /app -path "*/report*.jsonl" -o -path "*/logs/*" | sed -n "1,200p"'
- docker exec astro-project-backend-1 sh -lc 'tail -n 200 /app/logs/report.jsonl | grep -nE "week_brief|trace-weekbrief-rework-20260416|corr-weekbrief-rework-20260416|req-weekbrief-rework-20260416|packet_local|week_brief_packet_scope|week_brief_evidence_lane"'
- find logs artifacts prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC -type f \( -name '*.jsonl' -o -name '*.md' -o -name '*.json' -o -name '*.txt' \) -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort | tail -n 80
- docker exec astro-project-backend-1 sh -lc 'grep -n "trace-weekbrief-rework-20260416" /app/logs/report.jsonl && grep -n "req-weekbrief-rework-20260416" /app/logs/report.jsonl'
- find artifacts logs -type f \( -iname '*replay*' -o -iname '*digest*' -o -iname '*trace*' -o -iname '*review*' \) -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort | tail -n 80
- docker exec astro-project-backend-1 sh -lc 'python3 - <<"PY" ... PY'
- docker exec astro-project-backend-1 sh -lc 'grep -n "2026-04-16T13:37:39" /app/logs/report.jsonl | tail -n 20'

## Evidence Reviewed
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-BACKEND-ACTIVE-SLICE-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK.md
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /app/logs/report.jsonl:7319
- /app/logs/report.jsonl:7320
- /app/logs/report.jsonl:7321
- /app/logs/report.jsonl:7322
- /app/logs/report.jsonl:7323
- /app/logs/report.jsonl:7324
- /app/logs/report.jsonl:7325
- /app/logs/report.jsonl:7326
- /app/logs/report.jsonl:7327
- /app/logs/report.jsonl:7328
- /app/logs/report.jsonl:7329
- /app/logs/report.jsonl:7330
- /app/logs/report.jsonl:7331
- /app/logs/report.jsonl:7332
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/evidence/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-EVIDENCE.verification.md
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS.md

## Blocking Issues
- none
