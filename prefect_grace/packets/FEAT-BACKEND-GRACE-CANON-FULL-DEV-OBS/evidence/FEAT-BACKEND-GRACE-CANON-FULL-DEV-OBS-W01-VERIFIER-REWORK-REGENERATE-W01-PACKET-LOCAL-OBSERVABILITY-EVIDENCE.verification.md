# Verifier Evidence: FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01:packet:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE`

## Test Verdict
passed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- docker exec astro-project-backend-1 sh -lc 'python3 - <<"PY"
import json
from pathlib import Path
keys = {
    "feed": ["day_brief.built"],
    "report": ["week_brief.response_returned"],
    "scheduler": ["scheduler.sub_expired", "scheduler.sub_check.start"],
}
for name, events in keys.items():
    path = Path(f"/app/logs/{name}.jsonl")
    print(f"PATH {path} exists={path.exists()}")
    if not path.exists():
        continue
    matches = []
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("event") in events:
            matches.append(rec)
    print(f"MATCHES {name} {len(matches)}")
    for rec in matches[-3:]:
        print(json.dumps({
            "ts": rec.get("ts") or rec.get("timestamp"),
            "event": rec.get("event"),
            "module": rec.get("module"),
            "fn": rec.get("fn"),
            "block": rec.get("block"),
            "correlation_id": rec.get("correlation_id"),
            "trace_id": rec.get("trace_id"),
            "request_id": rec.get("request_id"),
            "report_id": rec.get("report_id"),
            "user_id": rec.get("user_id"),
        }, ensure_ascii=False, sort_keys=True))
PY'
- docker exec astro-project-backend-1 sh -lc 'python3 - <<"PY"
import json
from pathlib import Path
for name,event in [("feed","day_brief.built"),("report","week_brief.response_returned"),("scheduler","scheduler.sub_expired")]:
    path=Path(f"/app/logs/{name}.jsonl")
    rows=[]
    if path.exists():
        for line in path.read_text().splitlines():
            try: rec=json.loads(line)
            except Exception: continue
            if rec.get("event")==event and rec.get("trace_id") and rec.get("correlation_id") and rec.get("request_id"):
                rows.append(rec)
    print(f"{name}:{event}:attributed={len(rows)}")
    for rec in rows[-2:]:
        print(json.dumps({k:rec.get(k) for k in ["ts","timestamp","event","module","fn","block","correlation_id","trace_id","request_id","report_id","user_id"]}, sort_keys=True))
PY'

## Evidence Reviewed
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/evidence/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE.md
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /app/logs/feed.jsonl
- /app/logs/report.jsonl
- /app/logs/scheduler.jsonl

## Blocking Issues
- Analytics was not exercised by the packet-local command profile, so observability cannot be classified clean.
- Host-side post_test_review output still points at stale /opt/astro-project/logs rendered/read-surface evidence; fresh attributable IDs were confirmed only in container-local /app/logs artifacts.
