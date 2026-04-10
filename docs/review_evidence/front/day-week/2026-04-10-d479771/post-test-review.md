# Post-test observability gate — PASS_CLEAN

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — clean
- records_checked: 149
- last_timestamp: `2026-04-10T22:02:35.050729+00:00`
- fallback_count: 0
- sample_trace_id: `trace_19d796906fa_d8b07372`
- sample_correlation_id: `corr_19d796906b3_49638228`
- sample_request_id: `corr_19d796906b3_49638228`
- sample_report_id: `None`
- reason_codes: -
- alerts: -
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - feed.debug @ 2026-04-10T22:02:35.050382Z trace=trace_19d796b1855_65c86704 corr=corr_19d796b1829_70418a55 req=corr_19d796b1829_70418a55 report=- reason=-
  - day_brief.response_returned @ 2026-04-10T22:02:35.050729Z trace=trace_19d796b1855_65c86704 corr=corr_19d796b1829_70418a55 req=corr_19d796b1829_70418a55 report=- reason=-

## FLOW-TODAY-WEEK-WEEK — clean
- records_checked: 20
- last_timestamp: `2026-04-10T21:52:44.520663+00:00`
- fallback_count: 0
- sample_trace_id: `8249cdfd-7655-4c20-953b-1dc1c5219e74`
- sample_correlation_id: `71b69dae-539b-4150-9f2f-a7aac66c29e4`
- sample_request_id: `8249cdfd-7655-4c20-953b-1dc1c5219e74`
- sample_report_id: `77ed1b94-2d88-422b-a721-0d0084253ca6`
- reason_codes: -
- alerts: -
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - report.workflow.generation_complete @ 2026-04-10T21:52:44.519995Z trace=8e1fcc23-217e-4698-bd9e-667566be4451 corr=4cb33373-d6a4-4632-9b12-8d02b181758d req=8e1fcc23-217e-4698-bd9e-667566be4451 report=a444fc6b-0ec0-444c-844c-4adeaa2a9dd4 reason=-
  - report.workflow.generation_complete @ 2026-04-10T21:52:44.520663Z trace=8e1fcc23-217e-4698-bd9e-667566be4451 corr=4cb33373-d6a4-4632-9b12-8d02b181758d req=8e1fcc23-217e-4698-bd9e-667566be4451 report=a444fc6b-0ec0-444c-844c-4adeaa2a9dd4 reason=-

## Latest feed replay
{
  "events": [
    "request_success",
    "day_brief.response_returned",
    "request_start",
    "facts_start",
    "facts_cache_hit",
    "llm_prompt_path",
    "feed.block.start",
    "feed.block.end",
    "day_brief.built",
    "request_success",
    "day_brief.response_returned",
    "request_start",
    "facts_start",
    "facts_cache_hit",
    "llm_prompt_path",
    "feed.block.start",
    "feed.block.end",
    "day_brief.built",
    "request_success",
    "day_brief.response_returned"
  ],
  "auth": "telegram",
  "personalization_level": "personalized_v2",
  "prompt_path": "personalized_daily_v2",
  "fallback": false,
  "fallback_reason": null,
  "cache_hit": true,
  "cache_scope": "a2b38b8f2ccafa1a",
  "location": "London, UK",
  "timezone": "Europe/London"
}
