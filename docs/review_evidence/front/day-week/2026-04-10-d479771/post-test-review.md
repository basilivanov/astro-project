# Post-test observability gate — PASS_CLEAN

## Publication Metadata
- published_from_commit: `936d0a4`
- branch_head: `ab0929998c601247dc3b9d9f79745ffee2cb57a9`
- evidence_generated_at: `2026-04-10T22:12:41Z`
- proof_lane: `signed_telegram_today_real_backend + canonical_log_window`
- closeout_source: `tools/post_test_review.py --profile today-week --since 30m --report-format md`
- observability_closeout: `PASS_CLEAN`

## Public Ref Parity
- public_ref_verified_at: `2026-04-10T22:33:23Z`
- public_ref_verdict: `PUBLICLY_VERIFIED_CLEAN`
- verification_tool: `tools/publication/verify_day_public_ref.py`
- verification_scope: `exact commit + branch head + branch history + branch raw/blob evidence + signed proof spec`
- fail_closed_verdict: `FAIL_NO_PUBLIC_REF_PARITY`


- profile: `today-week`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`


## Day Text Layer Split
- packet: `PKT-DAY-TEXT-LAYER-SPLIT-2026-04-11`
- backend_text_layer: `description + why_astro_text` composed in `M-DAY-BRIEF-SERVICE`
- product_contract: `score + description + Что повлияло` per domain
- policy_gate: `description` stays human/non-technical; `why_astro_text` stays personalized astro and distinct from description
- observability_gate: post-test review now fails clean Today if text layer statuses or role policy reason codes are incomplete

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
