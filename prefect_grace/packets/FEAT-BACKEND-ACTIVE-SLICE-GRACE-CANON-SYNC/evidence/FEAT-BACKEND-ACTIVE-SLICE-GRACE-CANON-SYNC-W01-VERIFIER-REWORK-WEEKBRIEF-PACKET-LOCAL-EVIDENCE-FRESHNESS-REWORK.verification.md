# Verifier Evidence: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Test Verdict
passed

## Observability Verdict
clean

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format json
- docker exec astro-project-backend-1 sh -lc 'python3 - <<"PY"
from pathlib import Path
import json
path = Path("/app/logs/report.jsonl")
if not path.exists():
    print("MISSING /app/logs/report.jsonl")
    raise SystemExit(0)
rows = []
with path.open() as f:
    for lineno, line in enumerate(f, 1):
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("event") == "week_brief_built" and "trace-week-packet-" in str(row.get("trace_id", "")):
            rows.append((lineno, row))
for lineno, row in rows[-5:]:
    print(json.dumps({
        "path": "/app/logs/report.jsonl",
        "line": lineno,
        "timestamp": row.get("timestamp"),
        "event": row.get("event"),
        "module": row.get("module"),
        "fn": row.get("fn"),
        "block": row.get("block"),
        "trace_id": row.get("trace_id"),
        "correlation_id": row.get("correlation_id"),
        "request_id": row.get("request_id"),
        "report_id": row.get("report_id"),
        "week_brief_evidence_lane": row.get("week_brief_evidence_lane"),
        "week_brief_packet_scope": row.get("week_brief_packet_scope"),
        "week_brief_fallback_mode": row.get("week_brief_fallback_mode"),
        "chunk_parse_degraded": row.get("chunk_parse_degraded")
    }, ensure_ascii=False))
print(f"MATCH_COUNT={len(rows)}")
PY'

## Evidence Reviewed
- /opt/astro-project/tests/test_week_brief_service.py:540
- /app/logs/report.jsonl:7801
- /app/logs/report.jsonl:7683
- /opt/astro-project/logs/report.jsonl
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC.md
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/reviews/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK.review.md

## Blocking Issues
- none
