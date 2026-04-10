# Post-test observability gate — FAIL_NO_EVIDENCE

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — no-evidence-blocker
- records_checked: 0
- last_timestamp: `None`
- fallback_count: 0
- sample_trace_id: `None`
- sample_correlation_id: `None`
- sample_report_id: `None`
- reason_codes: -
- alerts: no recent today/day brief evidence, rendered summaries present without canonical logs
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, rendered evidence present but canonical source-of-truth evidence missing, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model

## FLOW-TODAY-WEEK-WEEK — no-evidence-blocker
- records_checked: 0
- last_timestamp: `None`
- fallback_count: 0
- sample_trace_id: `None`
- sample_correlation_id: `None`
- sample_report_id: `None`
- reason_codes: -
- alerts: no recent week/report evidence, rendered summaries present without canonical logs
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, rendered evidence present but canonical source-of-truth evidence missing, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
