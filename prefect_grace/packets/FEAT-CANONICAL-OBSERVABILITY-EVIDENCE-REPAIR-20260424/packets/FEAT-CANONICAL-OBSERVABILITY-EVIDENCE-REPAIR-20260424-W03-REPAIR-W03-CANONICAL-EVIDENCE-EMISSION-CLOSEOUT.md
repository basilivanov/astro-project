# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT

## Title
Repair W03 Canonical Evidence Emission Closeout

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT`

## Packet Type
rework

## Summary
Generate or repair the bounded canonical evidence path for Today, Week, Admin, and Catalog so W03 wave-final verification no longer ends in missing/stale evidence after green tests.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Write Scope
- tools/post_test_review.py only if the 30m window is incorrectly excluding request-bound records
- tools/log_watch/feed_admin_watch.py only if watcher freshness/provenance output is incomplete for current evidence
- tools/log_watch/forecast_catalog_watch.py only if watcher freshness/provenance output is incomplete for current evidence
- tests/test_post_test_review.py only for regression coverage of the identified W03 evidence-window issue
- tests/test_log_watch_feed_admin.py only for regression coverage of the identified Admin evidence issue
- tests/test_forecast_catalog_watch.py only for regression coverage of the identified Catalog evidence issue
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/packets/**

## Inputs
- W03 verifier evidence showing targeted tests passed and backend pipeline passed
- W03 verifier blocker: today-week post-test review returned FAIL_NO_EVIDENCE for Today and Week with records_checked=0
- W03 verifier note: logs/feed.jsonl contains recent Today request-bound identifiers at 2026-04-24T13:13:58Z but 30m review reported no records
- W03 verifier blocker: Admin watcher has no success evidence
- W03 verifier blocker: Catalog watcher success is stale from 2026-04-11T10:24:52.913782+00:00
- W03 reviewer conclusion that green tests and backend pipeline are insufficient for wave-final evidence gate

## Acceptance Criteria
- Diagnose whether Today/Week no-evidence is caused by stale runtime logs, wrong review window, wrong active log path, timestamp parsing, or missing canonical producer emission.
- If the issue is tooling-local, patch only the minimal post-test review/watcher code and add targeted regression tests.
- If the issue is producer/runtime-local and already covered by allowed backend logging-only exception, generate fresh canonical evidence using existing commands or the narrowest existing producer path without product behavior changes.
- Today and Week final post-test review must report clean, unexpected-degradation, or architect-approved degraded-but-expected; it must not report no-evidence-blocker when request-bound evidence exists.
- Admin and Catalog final watcher evidence must explicitly report fresh success or a concrete current producer absence/staleness reason with timestamps; stale evidence must not be ambiguous.
- Rerun targeted pytest, backend quick pipeline, today-week post-test review, read-only post-test review, Admin watcher, and Catalog watcher after the fix.
- Record final evidence artifact with command outputs, verdict, relevant trace_id/request_id/correlation_id/report_id when available, and explicit observability verdict.

## Verification Profile
- backend: python3 -m pytest tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py && docker exec astro-project-backend-1 python3 scripts/pipeline.py
- frontend: not required
- observability: wave_final: python3 tools/post_test_review.py --profile today-week --since 30m --report-format md && python3 tools/post_test_review.py --profile read-only --since 30m --report-format md && python3 tools/log_watch/feed_admin_watch.py --feed-log logs/feed.jsonl --admin-log logs/admin.jsonl --window-minutes 30 --limit 200 && python3 tools/log_watch/forecast_catalog_watch.py --catalog-log logs/catalog.jsonl --window-minutes 30 --limit 200

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- artifact_globs:
  - logs/*.jsonl
  - test-results/**/*.json
  - test-results/**/*.md
  - prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False
- rework_mode: bounded_fresh

## Reviewer Gate
- No frontend/UI work introduced.
- No product behavior, auth, pricing, or report schema redesign.
- No hidden degradation marked clean.
- No FAIL_NO_EVIDENCE for Today/Week when concrete request-bound evidence exists.
- Admin/Catalog evidence freshness is explicit and reviewer can distinguish stale, missing, and fresh evidence.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION

## Notes
- This is bounded coder rework, not planner work; packet topology does not change.
- Do not widen beyond W03 reviewer blockers.
- Use existing watcher/review helpers and existing canonical commands before adding any abstraction.
- If fresh Admin/Catalog producer evidence cannot be generated without business/product decisions, return the narrow blocker with exact command, log path, and missing event details instead of broad refactor.
- Frontend visual evidence remains not applicable.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W03",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "high",
  "title": "Repair W03 Canonical Evidence Emission Closeout",
  "summary": "Generate or repair the bounded canonical evidence path for Today, Week, Admin, and Catalog so W03 wave-final verification no longer ends in missing/stale evidence after green tests.",
  "write_scope": [
    "tools/post_test_review.py only if the 30m window is incorrectly excluding request-bound records",
    "tools/log_watch/feed_admin_watch.py only if watcher freshness/provenance output is incomplete for current evidence",
    "tools/log_watch/forecast_catalog_watch.py only if watcher freshness/provenance output is incomplete for current evidence",
    "tests/test_post_test_review.py only for regression coverage of the identified W03 evidence-window issue",
    "tests/test_log_watch_feed_admin.py only for regression coverage of the identified Admin evidence issue",
    "tests/test_forecast_catalog_watch.py only for regression coverage of the identified Catalog evidence issue",
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**",
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/packets/**"
  ],
  "inputs": [
    "W03 verifier evidence showing targeted tests passed and backend pipeline passed",
    "W03 verifier blocker: today-week post-test review returned FAIL_NO_EVIDENCE for Today and Week with records_checked=0",
    "W03 verifier note: logs/feed.jsonl contains recent Today request-bound identifiers at 2026-04-24T13:13:58Z but 30m review reported no records",
    "W03 verifier blocker: Admin watcher has no success evidence",
    "W03 verifier blocker: Catalog watcher success is stale from 2026-04-11T10:24:52.913782+00:00",
    "W03 reviewer conclusion that green tests and backend pipeline are insufficient for wave-final evidence gate"
  ],
  "acceptance_criteria": [
    "Diagnose whether Today/Week no-evidence is caused by stale runtime logs, wrong review window, wrong active log path, timestamp parsing, or missing canonical producer emission.",
    "If the issue is tooling-local, patch only the minimal post-test review/watcher code and add targeted regression tests.",
    "If the issue is producer/runtime-local and already covered by allowed backend logging-only exception, generate fresh canonical evidence using existing commands or the narrowest existing producer path without product behavior changes.",
    "Today and Week final post-test review must report clean, unexpected-degradation, or architect-approved degraded-but-expected; it must not report no-evidence-blocker when request-bound evidence exists.",
    "Admin and Catalog final watcher evidence must explicitly report fresh success or a concrete current producer absence/staleness reason with timestamps; stale evidence must not be ambiguous.",
    "Rerun targeted pytest, backend quick pipeline, today-week post-test review, read-only post-test review, Admin watcher, and Catalog watcher after the fix.",
    "Record final evidence artifact with command outputs, verdict, relevant trace_id/request_id/correlation_id/report_id when available, and explicit observability verdict."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py && docker exec astro-project-backend-1 python3 scripts/pipeline.py",
    "frontend": "not required",
    "observability": "wave_final: python3 tools/post_test_review.py --profile today-week --since 30m --report-format md && python3 tools/post_test_review.py --profile read-only --since 30m --report-format md && python3 tools/log_watch/feed_admin_watch.py --feed-log logs/feed.jsonl --admin-log logs/admin.jsonl --window-minutes 30 --limit 200 && python3 tools/log_watch/forecast_catalog_watch.py --catalog-log logs/catalog.jsonl --window-minutes 30 --limit 200"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "artifact_globs": [
      "logs/*.jsonl",
      "test-results/**/*.json",
      "test-results/**/*.md",
      "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false,
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "No frontend/UI work introduced.",
    "No product behavior, auth, pricing, or report schema redesign.",
    "No hidden degradation marked clean.",
    "No FAIL_NO_EVIDENCE for Today/Week when concrete request-bound evidence exists.",
    "Admin/Catalog evidence freshness is explicit and reviewer can distinguish stale, missing, and fresh evidence."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION"
  ],
  "notes": [
    "This is bounded coder rework, not planner work; packet topology does not change.",
    "Do not widen beyond W03 reviewer blockers.",
    "Use existing watcher/review helpers and existing canonical commands before adding any abstraction.",
    "If fresh Admin/Catalog producer evidence cannot be generated without business/product decisions, return the narrow blocker with exact command, log path, and missing event details instead of broad refactor.",
    "Frontend visual evidence remains not applicable."
  ],
  "parent_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
