### command: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
# Post-test observability gate — PASS_CLEAN

- profile: `read-only`
- analysis_window: `30m`
- logs_reviewed: `/opt/astro-project/logs/feed.jsonl`, `/opt/astro-project/logs/report.jsonl`

## FLOW-READ-SURFACE — clean
- records_checked: 2
- last_timestamp: `2026-04-01T22:46:08.202Z`
- fallback_count: 1
- sample_trace_id: `None`
- sample_correlation_id: `None`
- sample_request_id: `None`
- sample_report_id: `None`
- reason_codes: raw_chunk_text
- alerts: -
- rendered_presence: count=2 pass_modes=site_web site_web=True telegram_webapp=False parity_present=False
- rendered_statuses: passed
- rendered_assertion_classes: fallback_expected, rendered_hygiene
- rendered_parity_statuses: -
- rendered_verdict_notes: rendered evidence is additive and does not replace canonical logs/traces, canonical evidence clean; rendered evidence attached as supporting slice
- evidence_samples:
  - read_rendered_wave1_site_web_raw_chunk_fallback @ 2026-04-01T22:46:08.202Z trace=- corr=- req=- report=/read/read-rendered-wave1-site-web-fallback reason=raw_chunk_text
  - read_rendered_wave1_site_web_success @ 2026-04-01T22:46:06.992Z trace=- corr=- req=- report=/read/read-rendered-wave1-site-web-success reason=-
