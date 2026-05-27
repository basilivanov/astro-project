# Verifier Evidence: FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- wave_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01:packet:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND`

## Test Verdict
passed

## Observability Verdict
clean

## Frontend Visual Verdict
not_applicable

## Commands Run
- python3 scripts/generate_canonical_evidence.py --flows today,week,admin,catalog --window-minutes 30
- python3 -m pytest tests/test_canonical_evidence_generation.py tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py
- docker exec astro-project-backend-1 python3 scripts/pipeline.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- rg -n "canonical-(today|week|admin|catalog).*(913f030acc1d|0260b4daf790|b2d644896fe9|22e9ff5ffa05)|913f030acc1d|0260b4daf790|b2d644896fe9|22e9ff5ffa05" logs/feed.jsonl logs/report.jsonl logs/admin.jsonl logs/catalog.jsonl

## Evidence Reviewed
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/generate_canonical_evidence.out
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/targeted_pytest.out
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/backend_quick_pipeline.out
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/read_only_review.md
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/evidence_inspection.out
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/freshness_check.out
- logs/feed.jsonl
- logs/report.jsonl
- logs/admin.jsonl
- logs/catalog.jsonl
- test-results/evidence/rev-2026-02-10g/dev-health.json
- test-results/grace-report.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json
- prefect_grace/state/runs/20260424T150511Z-FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND-try1/last-message.md
- prefect_grace/state/runs/20260424T150511Z-FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T150511Z-FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND-try1/stderr.log
- logs/scheduler.jsonl
- logs/billing.jsonl
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/scope_status.out

## Blocking Issues
- none
