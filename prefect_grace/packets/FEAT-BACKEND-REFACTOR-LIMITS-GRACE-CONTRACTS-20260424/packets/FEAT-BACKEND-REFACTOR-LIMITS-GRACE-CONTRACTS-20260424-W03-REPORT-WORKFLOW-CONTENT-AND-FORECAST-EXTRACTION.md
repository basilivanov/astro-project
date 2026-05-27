# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION

## Title
Report Workflow Content And Forecast Extraction

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION`

## Packet Type
execution

## Summary
Extract cleanup, text processing, week/month forecast rendering, fallback content, template content, and model-resolution helpers from report_workflow.py.

## Wave
W03

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION`

## Write Scope
- backend/app/services/report_workflow.py
- backend/app/services/report_workflow_content*.py
- backend/app/services/report_workflow_forecast*.py
- tests/test_week_renderer.py
- tests/test_validation_template_fallback.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-GATE-W02
- report_workflow semantic block map
- content/fallback tests

## Acceptance Criteria
- Extracted modules are <=1000 lines
- Fallback/template output remains stable
- report_workflow facade exports prior helper names

## Verification Profile
- backend: targeted renderer/fallback pytest
- frontend: not required
- observability: packet_local workflow log review when emitted

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No report copy/schema semantic drift
- GRACE blocks align with extracted responsibilities

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-GATE-W02

## Notes
- Keep high-level generation lifecycle out of this packet.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Report Workflow Content And Forecast Extraction",
  "summary": "Extract cleanup, text processing, week/month forecast rendering, fallback content, template content, and model-resolution helpers from report_workflow.py.",
  "write_scope": [
    "backend/app/services/report_workflow.py",
    "backend/app/services/report_workflow_content*.py",
    "backend/app/services/report_workflow_forecast*.py",
    "tests/test_week_renderer.py",
    "tests/test_validation_template_fallback.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-GATE-W02",
    "report_workflow semantic block map",
    "content/fallback tests"
  ],
  "acceptance_criteria": [
    "Extracted modules are <=1000 lines",
    "Fallback/template output remains stable",
    "report_workflow facade exports prior helper names"
  ],
  "verification_profile": {
    "backend": "targeted renderer/fallback pytest",
    "frontend": "not required",
    "observability": "packet_local workflow log review when emitted"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No report copy/schema semantic drift",
    "GRACE blocks align with extracted responsibilities"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-GATE-W02"
  ],
  "notes": [
    "Keep high-level generation lifecycle out of this packet."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
