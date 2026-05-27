# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION

## Title
Report Workflow Chart Context And Insight Extraction

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION`

## Packet Type
execution

## Summary
Extract chart dispatch, report context assembly, section context, and natal insight-pack builders into cohesive <=1000-line modules.

## Wave
W03

## Role
coder

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION`

## Write Scope
- backend/app/services/report_workflow.py
- backend/app/services/report_workflow_chart*.py
- backend/app/services/report_workflow_context*.py
- backend/app/services/report_workflow_insight*.py
- tests/test_report_context.py
- tests/test_natal_section_context.py
- tests/test_canonical_astro_invariants.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION
- report context and natal section tests

## Acceptance Criteria
- Context/chart behavior remains stable
- Insight-pack helpers are split by cohesive domain
- Compatibility facade remains import-safe

## Verification Profile
- backend: targeted context/natal invariant pytest
- frontend: not required
- observability: packet_local workflow trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No astrology/chart calculation behavior changes
- No persistence or notification changes

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION

## Notes
- Use semantic extraction, not algorithm rewrites.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "xhigh",
  "title": "Report Workflow Chart Context And Insight Extraction",
  "summary": "Extract chart dispatch, report context assembly, section context, and natal insight-pack builders into cohesive <=1000-line modules.",
  "write_scope": [
    "backend/app/services/report_workflow.py",
    "backend/app/services/report_workflow_chart*.py",
    "backend/app/services/report_workflow_context*.py",
    "backend/app/services/report_workflow_insight*.py",
    "tests/test_report_context.py",
    "tests/test_natal_section_context.py",
    "tests/test_canonical_astro_invariants.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION",
    "report context and natal section tests"
  ],
  "acceptance_criteria": [
    "Context/chart behavior remains stable",
    "Insight-pack helpers are split by cohesive domain",
    "Compatibility facade remains import-safe"
  ],
  "verification_profile": {
    "backend": "targeted context/natal invariant pytest",
    "frontend": "not required",
    "observability": "packet_local workflow trace review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No astrology/chart calculation behavior changes",
    "No persistence or notification changes"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CONTENT-AND-FORECAST-EXTRACTION"
  ],
  "notes": [
    "Use semantic extraction, not algorithm rewrites."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
