# Post-test observability gate — FAIL_NO_EVIDENCE

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — clean
- records_checked: 69
- last_timestamp: `2026-04-10T20:54:37.528256+00:00`
- fallback_count: 0
- sample_trace_id: `f7dc5ec4-3b68-4c0a-9b81-b985d6ecea09`
- sample_correlation_id: `4a44d3e1-b2aa-4425-99a7-068477a93e00`
- sample_report_id: `None`
- reason_codes: telegram_auth_invalid
- alerts: today auth fallback detected
- rendered_presence: count=3 pass_modes=both,site_web,telegram_webapp site_web=True telegram_webapp=True parity_present=True
- rendered_statuses: passed
- rendered_assertion_classes: rendered_harness, rendered_hygiene, rendered_parity
- rendered_parity_statuses: pilot_dom_model_invariants, pilot_same_assertion_surface
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice, rendered parity metadata detected, rendered both/pass pilot semantics materialized without replacing wrapper verdict model
- evidence_samples:
  - day_brief.built @ 2026-04-10T20:54:09.186687Z trace=0c0c9cd6-663e-490e-a346-24e67a6d40c5 corr=bd3c5664-3de6-4af8-ba9e-7f7362de745c report=- reason=-
  - feed.debug @ 2026-04-10T20:54:09.187057Z trace=0c0c9cd6-663e-490e-a346-24e67a6d40c5 corr=bd3c5664-3de6-4af8-ba9e-7f7362de745c report=- reason=-
  - day_brief.response_returned @ 2026-04-10T20:54:09.187171Z trace=0c0c9cd6-663e-490e-a346-24e67a6d40c5 corr=bd3c5664-3de6-4af8-ba9e-7f7362de745c report=- reason=-

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

## Latest feed replay
{
  "events": [
    "day_brief.built",
    "request_success",
    "day_brief.response_returned",
    "request_start",
    "facts_start",
    "facts_built",
    "llm_prompt_path",
    "feed.block.start",
    "feed.block.end",
    "feed.block.start",
    "feed.block.start",
    "feed.semantic_blocks",
    "feed.block.end",
    "feed.block.end",
    "feed.block.start",
    "feed.generated",
    "feed.block.end",
    "day_brief.built",
    "request_success",
    "day_brief.response_returned"
  ],
  "auth": "telegram",
  "personalization_level": "personalized_v2",
  "prompt_path": "personalized_daily_v2",
  "fallback": true,
  "fallback_reason": null,
  "cache_hit": false,
  "cache_scope": "a340c9c14945c8bb",
  "location": "London, UK",
  "timezone": "Europe/London"
}
