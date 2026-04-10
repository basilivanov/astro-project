# Post-test observability gate — PASS_CLEAN

- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-TODAY-WEEK-TODAY — clean
- records_checked: 199
- last_timestamp: `2026-04-10T22:12:41.008639+00:00`
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
  - feed.debug @ 2026-04-10T22:12:41.008264Z trace=signed-today-real-1775859160023 corr=signed-today-real-1775859160023 req=signed-today-real-1775859160023 report=- reason=-
  - day_brief.response_returned @ 2026-04-10T22:12:41.008639Z trace=signed-today-real-1775859160023 corr=signed-today-real-1775859160023 req=signed-today-real-1775859160023 report=- reason=-

## FLOW-TODAY-WEEK-WEEK — clean
- records_checked: 10
- last_timestamp: `2026-04-10T21:52:44.520663+00:00`
- fallback_count: 0
- sample_trace_id: `8e1fcc23-217e-4698-bd9e-667566be4451`
- sample_correlation_id: `4cb33373-d6a4-4632-9b12-8d02b181758d`
- sample_request_id: `8e1fcc23-217e-4698-bd9e-667566be4451`
- sample_report_id: `a444fc6b-0ec0-444c-844c-4adeaa2a9dd4`
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
  "cache_scope": "be9b8434a3b46726",
  "location": "London, UK",
  "timezone": "Europe/London"
}

## Public Ref Parity — PASS
- public_ref_verified_at: `2026-04-10T22:20:35Z`
- public_ref_verdict: `pass`
- branch: `prod-release-20260327`
- branch_head: `8e63ec5ababefab53eccdc54e211fac411f3384c`
- published_from_commit: `936d0a4`
- dimensions:
  - commit_history: `branch_head_after_published_commit`
  - raw_readme_closeout: `pass`
  - blob_raw_closeout: `pass`
  - proof_lane: `pass`
  - raw_spec: `pass`
  - blob_spec: `pass`
