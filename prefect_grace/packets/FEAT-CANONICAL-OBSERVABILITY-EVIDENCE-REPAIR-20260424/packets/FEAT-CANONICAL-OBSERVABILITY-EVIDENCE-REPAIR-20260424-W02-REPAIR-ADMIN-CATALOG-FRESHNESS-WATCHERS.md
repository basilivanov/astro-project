# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS

## Title
Repair Admin/Catalog Freshness Watchers

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS`

## Packet Type
execution

## Summary
Update Admin/Catalog watcher freshness and provenance reporting with targeted tests.

## Wave
W02

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS`

## Write Scope
- tools/log_watch/common.py
- tools/log_watch/feed_admin_watch.py
- tools/log_watch/forecast_catalog_watch.py
- tests/test_log_watch_feed_admin.py
- tests/test_forecast_catalog_watch.py
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W00-ARCHITECT-FORMALIZATION
- current log watcher files
- current watcher tests

## Acceptance Criteria
- Fresh success, stale success, missing log, unreadable log, and error-after-success states are distinguishable.
- Admin and Catalog outputs include timestamp/context provenance for reviewer decisions.
- No permissions, auth, catalog, or admin product behavior changes.

## Verification Profile
- backend: python3 -m pytest tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py
- frontend: not required
- observability: packet_local watcher JSON/MD output from tests or fixtures

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Freshness/provenance semantics are explicit.
- No stale evidence silently passes as clean.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01

## Notes
- Prefer shared helpers only when both watcher files need the same local behavior.
- Escalate only if a real producer command is absent and cannot be represented as watcher provenance.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Repair Admin/Catalog Freshness Watchers",
  "summary": "Update Admin/Catalog watcher freshness and provenance reporting with targeted tests.",
  "write_scope": [
    "tools/log_watch/common.py",
    "tools/log_watch/feed_admin_watch.py",
    "tools/log_watch/forecast_catalog_watch.py",
    "tests/test_log_watch_feed_admin.py",
    "tests/test_forecast_catalog_watch.py",
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W00-ARCHITECT-FORMALIZATION",
    "current log watcher files",
    "current watcher tests"
  ],
  "acceptance_criteria": [
    "Fresh success, stale success, missing log, unreadable log, and error-after-success states are distinguishable.",
    "Admin and Catalog outputs include timestamp/context provenance for reviewer decisions.",
    "No permissions, auth, catalog, or admin product behavior changes."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py",
    "frontend": "not required",
    "observability": "packet_local watcher JSON/MD output from tests or fixtures"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Freshness/provenance semantics are explicit.",
    "No stale evidence silently passes as clean."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01"
  ],
  "notes": [
    "Prefer shared helpers only when both watcher files need the same local behavior.",
    "Escalate only if a real producer command is absent and cannot be represented as watcher provenance."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
