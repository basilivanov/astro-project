# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE

## Title
Constrain W01 Contract Alignment To Approved Scope

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE`

## Packet Type
rework

## Summary
Issue a bounded coder rework that removes frozen-scope and root-canon drift from W01 while preserving only the approved backend hub contract-alignment changes and refreshing packet-local evidence against the narrowed diff.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT`

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
- Target coder packet FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT
- Reviewer blocker notes identifying frozen-scope drift in /opt/astro-project/backend/app/services/week_brief_service.py
- Reviewer blocker notes identifying root GRACE canon edits outside W01 scope
- Latest W01 verifier evidence showing packet-local evidence is otherwise present

## Acceptance Criteria
- No remaining W01 diff exists outside the approved W01 write scope.
- No changes remain in /opt/astro-project/backend/app/services/week_brief_service.py for this packet.
- No root canon artifacts remain modified by W01.
- Scoped backend hub contract-alignment changes still satisfy the original W01 acceptance criteria without business-semantic drift.
- Backend quick and targeted W01 tests are rerun for the narrowed diff and packet-local observability verdict is refreshed.

## Verification Profile
- backend: backend:quick plus the targeted W01 hub pytest bundle after scope cleanup
- frontend: not required
- observability: packet_local read-only review refreshed after the rerun

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject any remaining frozen-scope drift.
- Reject any remaining root canon edits.
- Reject replacement edits whose only purpose is symmetry outside the approved hub slice.
- Require refreshed evidence tied to the cleaned W01 diff.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT

## Notes
- This is a local scope-containment fix; packet topology does not change.
- Coder should remove or revert only the out-of-scope W01 changes and keep compliant in-scope work intact.
- No planner escalation is needed because the blocker is bounded and execution-ready.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Constrain W01 Contract Alignment To Approved Scope",
  "summary": "Issue a bounded coder rework that removes frozen-scope and root-canon drift from W01 while preserving only the approved backend hub contract-alignment changes and refreshing packet-local evidence against the narrowed diff.",
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
    "Target coder packet FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
    "Reviewer blocker notes identifying frozen-scope drift in /opt/astro-project/backend/app/services/week_brief_service.py",
    "Reviewer blocker notes identifying root GRACE canon edits outside W01 scope",
    "Latest W01 verifier evidence showing packet-local evidence is otherwise present"
  ],
  "acceptance_criteria": [
    "No remaining W01 diff exists outside the approved W01 write scope.",
    "No changes remain in /opt/astro-project/backend/app/services/week_brief_service.py for this packet.",
    "No root canon artifacts remain modified by W01.",
    "Scoped backend hub contract-alignment changes still satisfy the original W01 acceptance criteria without business-semantic drift.",
    "Backend quick and targeted W01 tests are rerun for the narrowed diff and packet-local observability verdict is refreshed."
  ],
  "verification_profile": {
    "backend": "backend:quick plus the targeted W01 hub pytest bundle after scope cleanup",
    "frontend": "not required",
    "observability": "packet_local read-only review refreshed after the rerun"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Reject any remaining frozen-scope drift.",
    "Reject any remaining root canon edits.",
    "Reject replacement edits whose only purpose is symmetry outside the approved hub slice.",
    "Require refreshed evidence tied to the cleaned W01 diff."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT"
  ],
  "notes": [
    "This is a local scope-containment fix; packet topology does not change.",
    "Coder should remove or revert only the out-of-scope W01 changes and keep compliant in-scope work intact.",
    "No planner escalation is needed because the blocker is bounded and execution-ready."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
