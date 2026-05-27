# Verifier Evidence: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS`

## Test Verdict
failed

## Observability Verdict
clean

## Frontend Visual Verdict
not_applicable

## Commands Run
- sed -n '1,260p' prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS.md && printf '\n--- git status ---\n' && git status --short && printf '\n--- failure symbols ---\n' && rg -n "_join_sentence_parts|scene_seeds|executive_spec" backend/app/services tests/test_report_context.py tests/test_natal_section_context.py
- docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py
- docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py
- python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- wc -l backend/app/services/report_workflow*.py | sort -nr
- rg -n "FAILED|NameError|AssertionError|_normalize_status_variant|scene_seeds|short test summary" prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/targeted-report-pytest-rerun.log
- rg -n "PASS_CLEAN|FLOW-|fallback_count|sample_trace_id|sample_report_id|last_timestamp|alerts" prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/post-test-review-read-only-rerun.md
- find logs -maxdepth 1 -type f -name '*.jsonl' -print | sort
- find test-results -type f \( -name '*.json' -o -name '*.md' \) -print | sort | head -200
- find prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence -type f -print | sort

## Evidence Reviewed
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/packet-read-status.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/size-strict-rerun.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/targeted-report-pytest-rerun.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/canonical-pytest-rerun.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/post-test-review-read-only-rerun.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/report-workflow-line-counts-rerun.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/command-status-rerun.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/final-artifact-inspection.log
- logs/admin.jsonl
- logs/billing.jsonl
- logs/catalog.jsonl
- logs/feed.jsonl
- logs/report.jsonl
- logs/scheduler.jsonl
- test-results/grace-report.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_raw_chunk_fallback.json
- test-results/rendered-gate/FLOW-READ-SURFACE__read__read_rendered_wave1_site_web_success.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-TODAY-PREMIUM__today__today_rendered_wave1_telegram_webapp.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_both.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_site_web.json
- test-results/rendered-gate/FLOW-WEEK-BRIEF__week__week_rendered_wave1_telegram_webapp.json
- backend/app/reporting/section_templates.py
- prefect_grace/state/runs/20260424T161625Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS-try1/last-message.md
- prefect_grace/state/runs/20260424T161625Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS-try1/stdout.jsonl
- prefect_grace/state/runs/20260424T161625Z-FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS-try1/stderr.log
- test-results/evidence/rev-2026-02-10g/dev-health.json
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/canonical-pytest.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/observability-inspection.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/report-workflow-line-counts.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/artifact-glob-index.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/backend-pipeline.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/targeted-report-pytest.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/size-strict.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT/post-test-review-read-only.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS.verifier-20260424.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT.verification.md
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/canonical-pytest.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/command-status.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/observability-inspection.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/report-workflow-line-counts.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/targeted-report-pytest.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/size-strict.log
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS/post-test-review-read-only.md

## Blocking Issues
- Targeted W03 report pytest still fails: tests/test_natal_section_context.py::TestNatalSectionContext::test_facts_first_prompt_contract_and_validation
- executive_spec.prompt is missing required scene_seeds token
- The required prompt source is backend/app/reporting/section_templates.py, outside this packet write scope
