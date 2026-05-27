# Verifier Evidence: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Test Verdict
failed

## Observability Verdict
no-evidence-blocker

## Frontend Visual Verdict
not_applicable

## Commands Run
- sed -n '1,260p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.md && printf '\n--- dependency/evidence files ---\n' && find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424 -maxdepth 4 -type f | sort | sed -n '1,240p'
- wc -l backend/app/main.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- printf '%s\n' '--- logs mtimes ---'; find logs -maxdepth 1 -type f -name '*.jsonl' -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort; printf '%s\n' '--- recent test artifacts ---'; find test-results -type f \( -name '*.json' -o -name '*.md' \) -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort | tail -120; printf '%s\n' '--- feature evidence files ---'; find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort; printf '%s\n' '--- feed tail ---'; tail -n 30 logs/feed.jsonl 2>/dev/null || true; printf '%s\n' '--- report tail ---'; tail -n 40 logs/report.jsonl 2>/dev/null || true; printf '%s\n' '--- admin tail ---'; tail -n 30 logs/admin.jsonl 2>/dev/null || true; printf '%s\n' '--- catalog tail ---'; tail -n 30 logs/catalog.jsonl 2>/dev/null || true
- python3 - <<'PY'
import json, os
from pathlib import Path
for path in [Path('logs/feed.jsonl'), Path('logs/report.jsonl'), Path('logs/admin.jsonl'), Path('logs/catalog.jsonl')]:
    print(f'--- {path} ---')
    if not path.exists():
        print('missing')
        continue
    records=[]
    with path.open(errors='replace') as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    print('records', len(records), 'mtime', __import__('datetime').datetime.utcfromtimestamp(path.stat().st_mtime).isoformat()+'Z')
    for r in records[-3:]:
        print(json.dumps({k:r.get(k) for k in ['timestamp','event','trace_id','correlation_id','request_id','report_id','level','reason','reason_code','fallback_reason'] if r.get(k) is not None}, ensure_ascii=False))
PY
printf '\n--- W02 refresh evidence head ---\n'
sed -n '1,220p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md 2>/dev/null || true
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_api.py::test_api_gateway_declares_grace_module_contract_map_blocks_and_entrypoints

## Evidence Reviewed
- backend/app/main.py
- logs/feed.jsonl
- logs/report.jsonl
- logs/admin.jsonl
- logs/catalog.jsonl
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- test-results/grace-report.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/reviews/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.review.md
- prefect_grace/state/runs/20260424T132415Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/last-message.md
- prefect_grace/state/runs/20260424T132415Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T132415Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/stderr.log
- logs/scheduler.jsonl
- logs/billing.jsonl
- test-results/evidence/rev-2026-02-10g/dev-health.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md

## Blocking Issues
- today-week observability review failed with FAIL_NO_EVIDENCE
- Today flow remains no-evidence-blocker despite fresh trace/request/correlation samples
- Week flow remains unexpected-degradation due week/report chunk parse degraded fallback samples
- Admin evidence is stale: latest logs/admin.jsonl sample is 2026-03-22T15:36:36Z
- Catalog evidence is stale: latest logs/catalog.jsonl sample is 2026-04-11T10:24:52Z
- GRACE marker test fails because backend/app/main.py lacks START_BLOCK: API_GATEWAY_LOGGING
