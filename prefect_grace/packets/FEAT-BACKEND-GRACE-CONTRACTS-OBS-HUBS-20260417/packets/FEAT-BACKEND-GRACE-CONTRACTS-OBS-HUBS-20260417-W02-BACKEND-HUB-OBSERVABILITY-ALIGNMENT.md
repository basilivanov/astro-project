# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT

## Title
Backend Hub Observability Alignment

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT`

## Packet Type
execution

## Summary
Align dense backend hub observability and verdict tooling around module/fn/block/event and correlation landmarks.

## Wave
W02

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT`

## Write Scope
- /opt/astro-project/backend/app/main.py
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/backend/app/services/analytics.py
- /opt/astro-project/tools/post_test_review.py
- /opt/astro-project/tools/log_watch/common.py
- /opt/astro-project/tools/log_watch/scheduler_watch.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tests/test_catalog_logging.py
- /opt/astro-project/tests/test_billing_scheduler.py
- /opt/astro-project/tests/test_post_test_review.py

## Inputs
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-ARCHITECT-W01-GATE
- feature brief
- current hub logs and tooling baseline

## Acceptance Criteria
- Hub transitions emit or preserve stable module, fn, block, and correlation fields.
- Packet-local verdict tooling surfaces reviewer-readable hub landmarks.
- No new logging transport or business-semantic drift.

## Verification Profile
- backend: backend:quick plus logging/tooling pytest bundle
- frontend: not required
- observability: packet_local read-only review

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Tooling changes stay bounded to evidence readability.
- Do not alter today-week ownership rules.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-ARCHITECT-W01-GATE

## Notes
- Scheduler or analytics non-emission must be explicit.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Backend Hub Observability Alignment",
  "summary": "Align dense backend hub observability and verdict tooling around module/fn/block/event and correlation landmarks.",
  "write_scope": [
    "/opt/astro-project/backend/app/main.py",
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/backend/app/services/day_brief.py",
    "/opt/astro-project/backend/app/services/scheduler.py",
    "/opt/astro-project/backend/app/services/analytics.py",
    "/opt/astro-project/tools/post_test_review.py",
    "/opt/astro-project/tools/log_watch/common.py",
    "/opt/astro-project/tools/log_watch/scheduler_watch.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tests/test_catalog_logging.py",
    "/opt/astro-project/tests/test_billing_scheduler.py",
    "/opt/astro-project/tests/test_post_test_review.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-ARCHITECT-W01-GATE",
    "feature brief",
    "current hub logs and tooling baseline"
  ],
  "acceptance_criteria": [
    "Hub transitions emit or preserve stable module, fn, block, and correlation fields.",
    "Packet-local verdict tooling surfaces reviewer-readable hub landmarks.",
    "No new logging transport or business-semantic drift."
  ],
  "verification_profile": {
    "backend": "backend:quick plus logging/tooling pytest bundle",
    "frontend": "not required",
    "observability": "packet_local read-only review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Tooling changes stay bounded to evidence readability.",
    "Do not alter today-week ownership rules."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-ARCHITECT-W01-GATE"
  ],
  "notes": [
    "Scheduler or analytics non-emission must be explicit."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
