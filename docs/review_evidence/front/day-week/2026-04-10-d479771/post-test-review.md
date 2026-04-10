# Post-test observability gate — PASS_CLEAN

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — clean
- records_checked: 12
- last_timestamp: `2026-04-10T19:48:06.475449+00:00`
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
  - day_brief.built @ 2026-04-10T19:48:06.472673Z trace=- corr=- report=- reason=-
  - day_brief.built @ 2026-04-10T19:48:06.475449Z trace=- corr=- report=- reason=-

## FLOW-TODAY-WEEK-WEEK — clean
- records_checked: 10
- last_timestamp: `2026-04-10T19:48:43.986057+00:00`
- fallback_count: 0
- sample_trace_id: `8e2eebac-8723-4101-94e9-f8113b4e6c9f`
- sample_correlation_id: `dc77b6e6-20f1-45c8-8896-6768e79bd82f`
- sample_report_id: `00321883-8106-4091-9513-37bf03dc6a2d`
- reason_codes: -
- alerts: -
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - report.workflow.generation_complete @ 2026-04-10T19:48:43.985428Z trace=8e2eebac-8723-4101-94e9-f8113b4e6c9f corr=dc77b6e6-20f1-45c8-8896-6768e79bd82f report=00321883-8106-4091-9513-37bf03dc6a2d reason=-
  - report.workflow.generation_complete @ 2026-04-10T19:48:43.986057Z trace=8e2eebac-8723-4101-94e9-f8113b4e6c9f corr=dc77b6e6-20f1-45c8-8896-6768e79bd82f report=00321883-8106-4091-9513-37bf03dc6a2d reason=-

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
