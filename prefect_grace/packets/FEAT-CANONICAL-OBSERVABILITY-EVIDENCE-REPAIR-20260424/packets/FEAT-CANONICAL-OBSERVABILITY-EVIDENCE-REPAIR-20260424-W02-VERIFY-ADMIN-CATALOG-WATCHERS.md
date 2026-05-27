# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS

## Title
Verify Admin/Catalog Watchers

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS`

## Packet Type
execution

## Summary
Run targeted watcher tests and capture freshness/provenance verdict evidence.

## Wave
W02

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- coder_w02_admin_catalog_watchers output

## Acceptance Criteria
- Watcher tests pass.
- Verifier evidence shows stale and missing evidence are distinguishable.
- Verifier records whether any producer-side absence remains.

## Verification Profile
- backend: python3 -m pytest tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py
- frontend: not required
- observability: packet_local watcher evidence

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

## Reviewer Gate
- Evidence includes commands and provenance verdict.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS

## Notes
- No frontend verification required.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Admin/Catalog Watchers",
  "summary": "Run targeted watcher tests and capture freshness/provenance verdict evidence.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "coder_w02_admin_catalog_watchers output"
  ],
  "acceptance_criteria": [
    "Watcher tests pass.",
    "Verifier evidence shows stale and missing evidence are distinguishable.",
    "Verifier records whether any producer-side absence remains."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py",
    "frontend": "not required",
    "observability": "packet_local watcher evidence"
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
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence includes commands and provenance verdict."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS"
  ],
  "notes": [
    "No frontend verification required."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
