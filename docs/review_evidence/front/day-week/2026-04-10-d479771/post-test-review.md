# Post-test observability gate — PASS_CLEAN

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — clean
- records_checked: 30
- last_timestamp: `2026-04-10T21:34:04.108891+00:00`
- fallback_count: 0
- sample_trace_id: `None`
- sample_correlation_id: `None`
- sample_report_id: `None`
- reason_codes: -
- alerts: -
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - day_brief.built @ 2026-04-10T21:34:04.106667Z trace=- corr=- report=- reason=-
  - day_brief.built @ 2026-04-10T21:34:04.108891Z trace=- corr=- report=- reason=-

## FLOW-TODAY-WEEK-WEEK — clean
- records_checked: 10
- last_timestamp: `2026-04-10T21:34:38.353813+00:00`
- fallback_count: 0
- sample_trace_id: `8249cdfd-7655-4c20-953b-1dc1c5219e74`
- sample_correlation_id: `71b69dae-539b-4150-9f2f-a7aac66c29e4`
- sample_report_id: `77ed1b94-2d88-422b-a721-0d0084253ca6`
- reason_codes: -
- alerts: -
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - report.workflow.generation_complete @ 2026-04-10T21:34:38.353118Z trace=8249cdfd-7655-4c20-953b-1dc1c5219e74 corr=71b69dae-539b-4150-9f2f-a7aac66c29e4 report=77ed1b94-2d88-422b-a721-0d0084253ca6 reason=-
  - report.workflow.generation_complete @ 2026-04-10T21:34:38.353813Z trace=8249cdfd-7655-4c20-953b-1dc1c5219e74 corr=71b69dae-539b-4150-9f2f-a7aac66c29e4 report=77ed1b94-2d88-422b-a721-0d0084253ca6 reason=-

## Latest feed replay
{
  "events": [
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built",
    "day_brief.built"
  ],
  "auth": null,
  "personalization_level": "personalized_v2",
  "prompt_path": null,
  "fallback": false,
  "fallback_reason": null,
  "cache_hit": false,
  "cache_scope": null,
  "location": null,
  "timezone": null
}
