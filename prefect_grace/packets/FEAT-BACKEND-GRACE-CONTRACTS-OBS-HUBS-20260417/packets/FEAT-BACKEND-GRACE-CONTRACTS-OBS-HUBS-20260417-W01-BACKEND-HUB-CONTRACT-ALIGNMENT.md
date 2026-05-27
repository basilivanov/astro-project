# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT

## Title
Backend Hub Contract Alignment

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT`

## Packet Type
execution

## Summary
Close or confirm residual strict-GRACE addressability gaps on scoped backend hub files and tests.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT`

## Write Scope
- /opt/astro-project/backend/app/main.py
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/backend/app/middleware/correlation.py
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/backend/app/services/day_brief_validators.py
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/backend/app/services/analytics.py
- /opt/astro-project/tests/test_day_brief.py
- /opt/astro-project/tests/test_day_brief_schema.py
- /opt/astro-project/tests/test_week_brief_api.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tests/test_billing_scheduler.py
- /opt/astro-project/tests/test_catalog_logging.py

## Inputs
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W00-ARCHITECT-FORMALIZATION
- feature brief
- current backend hub baseline

## Acceptance Criteria
- Residual hub addressability gaps are closed or explicitly proven already satisfied.
- Targeted tests lock the scoped hub markers and contract shape.
- No business semantic drift.

## Verification Profile
- backend: backend:quick plus targeted hub pytest bundle
- frontend: not required
- observability: packet_local read-only review

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- No frozen-scope drift.
- No root canon edits.
- No rewrite for symmetry when tests can prove current compliance.

## Dependencies
-

## Notes
- Planner remains off.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Backend Hub Contract Alignment",
  "summary": "Close or confirm residual strict-GRACE addressability gaps on scoped backend hub files and tests.",
  "write_scope": [
    "/opt/astro-project/backend/app/main.py",
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/backend/app/middleware/correlation.py",
    "/opt/astro-project/backend/app/services/day_brief.py",
    "/opt/astro-project/backend/app/services/day_brief_validators.py",
    "/opt/astro-project/backend/app/services/scheduler.py",
    "/opt/astro-project/backend/app/services/analytics.py",
    "/opt/astro-project/tests/test_day_brief.py",
    "/opt/astro-project/tests/test_day_brief_schema.py",
    "/opt/astro-project/tests/test_week_brief_api.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tests/test_billing_scheduler.py",
    "/opt/astro-project/tests/test_catalog_logging.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "current backend hub baseline"
  ],
  "acceptance_criteria": [
    "Residual hub addressability gaps are closed or explicitly proven already satisfied.",
    "Targeted tests lock the scoped hub markers and contract shape.",
    "No business semantic drift."
  ],
  "verification_profile": {
    "backend": "backend:quick plus targeted hub pytest bundle",
    "frontend": "not required",
    "observability": "packet_local read-only review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "No frozen-scope drift.",
    "No root canon edits.",
    "No rewrite for symmetry when tests can prove current compliance."
  ],
  "dependencies": [],
  "notes": [
    "Planner remains off."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
