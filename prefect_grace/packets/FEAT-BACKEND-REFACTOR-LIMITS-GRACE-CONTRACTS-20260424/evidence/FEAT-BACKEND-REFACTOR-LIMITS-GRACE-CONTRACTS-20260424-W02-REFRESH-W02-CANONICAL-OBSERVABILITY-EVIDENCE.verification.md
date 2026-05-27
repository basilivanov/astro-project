# Verifier Evidence: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Test Verdict
failed

## Observability Verdict
no-evidence-blocker

## Frontend Visual Verdict
not_applicable

## Commands Run
- sed -n '1,260p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.md && printf '\n--- evidence files ---\n' && find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424 -maxdepth 4 -type f | sort | sed -n '1,220p'
- printf '%s\n' '--- rework evidence candidates ---'; find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence -type f -maxdepth 1 -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort; printf '%s\n' '--- relevant reviews ---'; sed -n '1,240p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/reviews/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.review.md 2>/dev/null || true; printf '%s\n' '--- main line count ---'; wc -l backend/app/main.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py tests/test_admin_api.py tests/test_daily_feed_robustness.py tests/test_week_brief_api.py
- python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- printf '%s\n' '--- logs mtimes ---'; find logs -maxdepth 1 -type f -name '*.jsonl' -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort; printf '%s\n' '--- test artifacts recent ---'; find test-results -type f \( -name '*.json' -o -name '*.md' \) -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort | tail -120; printf '%s\n' '--- feature evidence files ---'; find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort; printf '%s\n' '--- feed tail ---'; tail -n 40 logs/feed.jsonl 2>/dev/null || true; printf '%s\n' '--- report tail ---'; tail -n 60 logs/report.jsonl 2>/dev/null || true; printf '%s\n' '--- admin tail ---'; tail -n 60 logs/admin.jsonl 2>/dev/null || true; printf '%s\n' '--- catalog tail ---'; tail -n 60 logs/catalog.jsonl 2>/dev/null || true
- date -u '+%Y-%m-%dT%H:%M:%SZ'; rg -n "FLOW-TODAY|today-week|week/report chunk|signed proof|why_missing|no-evidence" tools/post_test_review.py backend tests -S | sed -n '1,220p'; printf '\n--- relevant fresh log summary ---\n'; python3 - <<'PY' ... PY
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py && docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py
- python3 tools/post_test_review.py --profile today-week --since 30m --report-format md; status=$?; printf '\nEXIT_STATUS=%s\n' "$status"; python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; status=$?; printf '\nREAD_ONLY_EXIT_STATUS=%s\n' "$status"

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
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/reviews/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.review.md
- prefect_grace/state/runs/20260424T132108Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/last-message.md
- prefect_grace/state/runs/20260424T132108Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T132108Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE-try1/stderr.log
- logs/scheduler.jsonl
- logs/billing.jsonl
- test-results/evidence/rev-2026-02-10g/dev-health.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md

## Blocking Issues
- today-week observability review failed with FAIL_NO_EVIDENCE
- Today flow remains no-evidence-blocker despite trace/request/correlation samples
- Week flow remains unexpected-degradation due week/report chunk parse degraded fallback samples
- Admin evidence is stale: latest logs/admin.jsonl sample is 2026-03-22T15:36:36Z
- Catalog evidence is stale: latest logs/catalog.jsonl sample is 2026-04-11T10:24:52Z
- Refresh producer command failed in tests/test_week_brief_api.py on missing START_BLOCK: API_GATEWAY_LOGGING in backend/app/main.py
