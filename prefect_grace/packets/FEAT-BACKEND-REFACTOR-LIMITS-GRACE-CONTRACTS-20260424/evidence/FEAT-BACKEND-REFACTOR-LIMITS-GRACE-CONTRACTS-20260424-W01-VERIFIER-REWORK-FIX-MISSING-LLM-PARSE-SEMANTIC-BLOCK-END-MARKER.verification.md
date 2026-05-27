# Verifier Evidence: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER`

## Test Verdict
passed

## Observability Verdict
degraded-but-expected

## Frontend Visual Verdict
not_applicable

## Commands Run
- sed -n '1,220p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.md && printf '\n--- dependency rework evidence ---\n' && sed -n '1,220p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md 2>/dev/null || true && printf '\n--- marker grep ---\n' && grep -n 'START_BLOCK\|END_BLOCK\|MODULE_CONTRACT\|MODULE_MAP' backend/app/llm/orchestrator_parse.py && printf '\n--- marker pairing check ---\n' && python3 - <<'PY' ... PY && wc -l backend/app/llm/*.py backend/app/services/week_brief*.py | sort -n
- docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/main.py backend/app/services/report_workflow.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_llm_cli_parsing.py tests/test_llm_fallback_chain.py tests/test_llm_model_routing.py tests/test_week_brief_service.py tests/test_week_brief_api.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- find logs -maxdepth 1 -type f -name '*.jsonl' -print | sort; find test-results -type f \( -name '*.json' -o -name '*.md' \) -print | sort | head -120; find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence -type f -print 2>/dev/null | sort || true; grep -n 'week_brief\|LLM_PARSE\|llm.invalid' logs/report.jsonl 2>/dev/null | tail -20 || true; docker exec astro-project-backend-1 sh -lc 'grep -n "week_brief\|LLM_PARSE\|llm.invalid" /app/logs/report.jsonl 2>/dev/null | tail -20 || true'; git status --short backend/app/llm/orchestrator_parse.py prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424

## Evidence Reviewed
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- backend/app/llm/orchestrator_parse.py:51
- backend/app/llm/orchestrator_parse.py:951
- logs/report.jsonl
- /app/logs/report.jsonl
- logs/feed.jsonl
- logs/admin.jsonl
- logs/catalog.jsonl
- logs/scheduler.jsonl
- logs/billing.jsonl
- test-results/grace-report.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json
- prefect_grace/state/runs/20260424T125052Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER-try1/last-message.md
- prefect_grace/state/runs/20260424T125052Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T125052Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER-try1/stderr.log
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- test-results/evidence/rev-2026-02-10g/dev-health.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verification.md

## Blocking Issues
- none
