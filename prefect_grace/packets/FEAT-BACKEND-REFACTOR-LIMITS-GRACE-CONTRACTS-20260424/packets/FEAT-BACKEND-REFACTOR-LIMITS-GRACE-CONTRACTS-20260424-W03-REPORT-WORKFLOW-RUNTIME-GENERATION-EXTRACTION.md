# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION

## Title
Report Workflow Runtime Generation Extraction

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION`

## Packet Type
execution

## Summary
Extract run lifecycle, chunk initialization, section generation, report generation, delivery notification, and workflow logging while preserving monkeypatch-compatible facade symbols.

## Wave
W03

## Role
coder

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION`

## Write Scope
- backend/app/services/report_workflow.py
- backend/app/services/report_workflow_runtime*.py
- backend/app/services/report_workflow_logging*.py
- tests/test_report_workflow_regression.py
- tests/test_report_threshold.py
- tests/test_json_pipeline.py
- tests/test_backend_grace_wave_finish.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION
- workflow regression tests

## Acceptance Criteria
- report_workflow.py is <=1000 lines
- ReportRun/ReportChunk status transitions are unchanged
- Workflow logs keep module/contract/block/report_id attribution

## Verification Profile
- backend: targeted workflow pytest plus backend quick candidate
- frontend: not required
- observability: wave_final report/today-week log review; clean required

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No async lifecycle regression
- No notification side-effect regression
- No loss of report workflow trace fields

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION

## Notes
- If facade monkeypatch compatibility is impossible for a symbol, add a targeted test and document the local test-boundary update.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "xhigh",
  "title": "Report Workflow Runtime Generation Extraction",
  "summary": "Extract run lifecycle, chunk initialization, section generation, report generation, delivery notification, and workflow logging while preserving monkeypatch-compatible facade symbols.",
  "write_scope": [
    "backend/app/services/report_workflow.py",
    "backend/app/services/report_workflow_runtime*.py",
    "backend/app/services/report_workflow_logging*.py",
    "tests/test_report_workflow_regression.py",
    "tests/test_report_threshold.py",
    "tests/test_json_pipeline.py",
    "tests/test_backend_grace_wave_finish.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION",
    "workflow regression tests"
  ],
  "acceptance_criteria": [
    "report_workflow.py is <=1000 lines",
    "ReportRun/ReportChunk status transitions are unchanged",
    "Workflow logs keep module/contract/block/report_id attribution"
  ],
  "verification_profile": {
    "backend": "targeted workflow pytest plus backend quick candidate",
    "frontend": "not required",
    "observability": "wave_final report/today-week log review; clean required"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No async lifecycle regression",
    "No notification side-effect regression",
    "No loss of report workflow trace fields"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-CHART-CONTEXT-AND-INSIGHT-EXTRACTION"
  ],
  "notes": [
    "If facade monkeypatch compatibility is impossible for a symbol, add a targeted test and document the local test-boundary update."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
