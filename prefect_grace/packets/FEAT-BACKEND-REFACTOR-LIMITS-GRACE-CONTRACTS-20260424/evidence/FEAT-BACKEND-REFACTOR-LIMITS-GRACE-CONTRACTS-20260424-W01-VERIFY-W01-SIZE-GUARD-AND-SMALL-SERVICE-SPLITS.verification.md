# Verifier Evidence: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS`

## Test Verdict
passed

## Observability Verdict
clean

## Frontend Visual Verdict
not_applicable

## Commands Run
- docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/main.py backend/app/services/report_workflow.py && docker exec astro-project-backend-1 python3 -m pytest -q tests/test_llm_cli_parsing.py tests/test_llm_fallback_chain.py tests/test_llm_model_routing.py tests/test_week_brief_service.py tests/test_week_brief_api.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- wc -l backend/app/llm/*.py backend/app/services/week_brief*.py | sort -nr | head -40
- grep -iE 'week_brief|week brief|trace-week' logs/report.jsonl 2>/dev/null | tail -20 || true
- tail -200 logs/report.jsonl 2>/dev/null | grep -iE 'week_brief|fallback|degrad|error|exception|trace-week' | tail -40 || true

## Evidence Reviewed
- /opt/astro-project/logs/feed.jsonl
- /opt/astro-project/logs/report.jsonl
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- /opt/astro-project/test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verifier-20260424.md
- trace_id: canonical-week-trace-b27b712f5ac7
- report_id: canonical-week-report-b27b712f5ac7
- request_id: canonical-week-request-b27b712f5ac7
- prefect_grace/state/runs/20260424T153124Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS-try1/last-message.md
- prefect_grace/state/runs/20260424T153124Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T153124Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS-try1/stderr.log
- logs/report.jsonl
- logs/feed.jsonl
- logs/admin.jsonl
- logs/catalog.jsonl
- logs/scheduler.jsonl
- logs/billing.jsonl
- test-results/grace-report.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- test-results/evidence/rev-2026-02-10g/dev-health.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verifier-20260424.md

## Blocking Issues
- none
