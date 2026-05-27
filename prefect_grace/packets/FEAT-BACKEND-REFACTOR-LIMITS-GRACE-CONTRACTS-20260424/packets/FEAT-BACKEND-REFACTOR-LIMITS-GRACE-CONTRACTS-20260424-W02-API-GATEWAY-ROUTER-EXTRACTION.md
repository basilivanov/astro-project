# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION

## Title
API Gateway Router Extraction

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION`

## Packet Type
execution

## Summary
Move admin, report, user/profile, feed/week/day, diagnostics, and geo endpoints from main.py into routers while preserving app route table and compatibility exports.

## Wave
W02

## Role
coder

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION`

## Write Scope
- backend/app/main.py
- backend/app/routers/*.py
- tests/test_admin_api.py
- tests/test_daily_feed_robustness.py
- tests/test_access_control_integration.py
- tests/test_catalog_logging.py
- tests/test_backend_grace_wave_finish.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION
- existing route tests and monkeypatch paths

## Acceptance Criteria
- main.py is <=1000 lines
- All routes remain registered with same paths/methods/status behavior
- Compatibility exports cover existing local imports where practical
- Auth and access-control behavior remain unchanged

## Verification Profile
- backend: targeted API/admin/feed/catalog/access pytest plus backend quick if route table changes are broad
- frontend: not required
- observability: wave_final today-week post-test review plus structured Admin/Catalog log inspection

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No auth dependency weakening
- No billing/access-control semantic drift
- No silent route removal

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION

## Notes
- Patch paths may move only when external behavior remains unchanged and tests document the new boundary.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "xhigh",
  "title": "API Gateway Router Extraction",
  "summary": "Move admin, report, user/profile, feed/week/day, diagnostics, and geo endpoints from main.py into routers while preserving app route table and compatibility exports.",
  "write_scope": [
    "backend/app/main.py",
    "backend/app/routers/*.py",
    "tests/test_admin_api.py",
    "tests/test_daily_feed_robustness.py",
    "tests/test_access_control_integration.py",
    "tests/test_catalog_logging.py",
    "tests/test_backend_grace_wave_finish.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION",
    "existing route tests and monkeypatch paths"
  ],
  "acceptance_criteria": [
    "main.py is <=1000 lines",
    "All routes remain registered with same paths/methods/status behavior",
    "Compatibility exports cover existing local imports where practical",
    "Auth and access-control behavior remain unchanged"
  ],
  "verification_profile": {
    "backend": "targeted API/admin/feed/catalog/access pytest plus backend quick if route table changes are broad",
    "frontend": "not required",
    "observability": "wave_final today-week post-test review plus structured Admin/Catalog log inspection"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No auth dependency weakening",
    "No billing/access-control semantic drift",
    "No silent route removal"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION"
  ],
  "notes": [
    "Patch paths may move only when external behavior remains unchanged and tests document the new boundary."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
