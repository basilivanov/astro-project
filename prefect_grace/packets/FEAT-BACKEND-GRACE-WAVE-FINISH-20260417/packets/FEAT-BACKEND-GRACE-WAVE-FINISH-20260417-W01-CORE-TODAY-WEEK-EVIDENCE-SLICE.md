# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE

## Title
Core Today Week Evidence Slice

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE`

## Packet Type
execution

## Summary
Repair only bounded core Today/Week attribution gaps and add/update the targeted current-run evidence test.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
-

## Write Scope
- /opt/astro-project/backend/app/main.py
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/tests/test_backend_grace_wave_finish.py
- /opt/astro-project/tests/test_day_brief.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tools/post_test_review.py

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W00-ARCHITECT-FORMALIZATION
- feature brief
- prefect_grace/briefs/backend_grace_wave_finish_20260417.yaml

## Acceptance Criteria
- Today/Week evidence can be emitted by a targeted backend test with current-run ids.
- DayBrief evidence uses declared stable block naming or the declared block map is updated locally.
- No business behavior changes are introduced.

## Verification Profile
- backend: Run backend:quick and targeted core evidence pytest.
- frontend: not applicable
- observability: Run read-only packet-local review after tests.

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- No scope drift into scheduler, analytics, frontend, report_workflow, or WeekBrief service code.
- No canonical today-week closeout claim from W01.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W00-ARCHITECT-FORMALIZATION

## Notes
- Use week_brief_service.py only as a style reference.
- If current code already satisfies a marker, do not churn it.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Core Today Week Evidence Slice",
  "summary": "Repair only bounded core Today/Week attribution gaps and add/update the targeted current-run evidence test.",
  "write_scope": [
    "/opt/astro-project/backend/app/main.py",
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/backend/app/services/day_brief.py",
    "/opt/astro-project/tests/test_backend_grace_wave_finish.py",
    "/opt/astro-project/tests/test_day_brief.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tools/post_test_review.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "prefect_grace/briefs/backend_grace_wave_finish_20260417.yaml"
  ],
  "acceptance_criteria": [
    "Today/Week evidence can be emitted by a targeted backend test with current-run ids.",
    "DayBrief evidence uses declared stable block naming or the declared block map is updated locally.",
    "No business behavior changes are introduced."
  ],
  "verification_profile": {
    "backend": "Run backend:quick and targeted core evidence pytest.",
    "frontend": "not applicable",
    "observability": "Run read-only packet-local review after tests."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "No scope drift into scheduler, analytics, frontend, report_workflow, or WeekBrief service code.",
    "No canonical today-week closeout claim from W01."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W00-ARCHITECT-FORMALIZATION"
  ],
  "notes": [
    "Use week_brief_service.py only as a style reference.",
    "If current code already satisfies a marker, do not churn it."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
