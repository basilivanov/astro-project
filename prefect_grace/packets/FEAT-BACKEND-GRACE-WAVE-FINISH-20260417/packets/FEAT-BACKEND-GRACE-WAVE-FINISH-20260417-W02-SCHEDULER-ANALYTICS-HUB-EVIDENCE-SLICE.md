# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE

## Title
Scheduler Analytics Hub Evidence Slice

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE`

## Packet Type
execution

## Summary
Repair only bounded scheduler/analytics hub attribution or read-only review gaps and extend targeted evidence tests.

## Wave
W02

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
-

## Write Scope
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/backend/app/services/analytics.py
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/tests/test_backend_grace_wave_finish.py
- /opt/astro-project/tests/test_billing_scheduler.py
- /opt/astro-project/tests/test_catalog_logging.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tests/test_post_test_review.py
- /opt/astro-project/tools/post_test_review.py

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-ARCHITECT-GATE-CORE-EVIDENCE
- feature brief

## Acceptance Criteria
- Scheduler and analytics hub evidence is fresh and attributable when exercised.
- Non-emission is explicitly classified when expected.
- No scheduler cadence or analytics schema behavior changes.

## Verification Profile
- backend: Run backend:quick and targeted hub pytest.
- frontend: not applicable
- observability: Run read-only packet-local review after tests.

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- No drift into main.py, DayBrief, WeekBrief, report_workflow, or frontend.
- No final canonical closeout claim from W02.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-ARCHITECT-GATE-CORE-EVIDENCE

## Notes
- Prefer fixing the local emitter/test freshness over widening tooling.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Scheduler Analytics Hub Evidence Slice",
  "summary": "Repair only bounded scheduler/analytics hub attribution or read-only review gaps and extend targeted evidence tests.",
  "write_scope": [
    "/opt/astro-project/backend/app/services/scheduler.py",
    "/opt/astro-project/backend/app/services/analytics.py",
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/tests/test_backend_grace_wave_finish.py",
    "/opt/astro-project/tests/test_billing_scheduler.py",
    "/opt/astro-project/tests/test_catalog_logging.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tests/test_post_test_review.py",
    "/opt/astro-project/tools/post_test_review.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-ARCHITECT-GATE-CORE-EVIDENCE",
    "feature brief"
  ],
  "acceptance_criteria": [
    "Scheduler and analytics hub evidence is fresh and attributable when exercised.",
    "Non-emission is explicitly classified when expected.",
    "No scheduler cadence or analytics schema behavior changes."
  ],
  "verification_profile": {
    "backend": "Run backend:quick and targeted hub pytest.",
    "frontend": "not applicable",
    "observability": "Run read-only packet-local review after tests."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "No drift into main.py, DayBrief, WeekBrief, report_workflow, or frontend.",
    "No final canonical closeout claim from W02."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-ARCHITECT-GATE-CORE-EVIDENCE"
  ],
  "notes": [
    "Prefer fixing the local emitter/test freshness over widening tooling."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
