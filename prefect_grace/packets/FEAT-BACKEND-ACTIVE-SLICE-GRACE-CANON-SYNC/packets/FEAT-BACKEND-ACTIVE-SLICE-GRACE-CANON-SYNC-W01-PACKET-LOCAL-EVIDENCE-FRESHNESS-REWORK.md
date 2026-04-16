# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Title
Packet-Local Evidence Freshness Rework

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Packet Type
rework

## Summary
Issue a bounded fresh coder rework to make W01 packet-local read-only observability evidence attributable to the current verifier run. Backend behavior is already green; the rework must produce or expose fresh packet-local trace_id/request_id/report_id evidence for the exercised backend active-slice flow without claiming canonical today-week closeout.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Write Scope
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/tests/test_week_brief_service.py
- /opt/astro-project/tests/test_week_brief_api.py
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET.md

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md
- Reviewer blocker: backend quick and targeted pytest passed, but read-only observability evidence was stale and lacked current-run trace_id/request_id/report_id attribution.

## Acceptance Criteria
- Diff remains inside the declared write scope.
- WeekBrief payload, envelope, fallback, API, Day/Week business semantics, and scoring behavior remain unchanged.
- Targeted WeekBrief tests and backend quick remain green.
- A current verifier run can produce or identify fresh packet-local evidence with stable module/function/block attribution and current trace_id/request_id/report_id values.
- The packet keeps W01 observability ownership as packet_local and does not require or claim canonical today-week closeout.

## Verification Profile
- backend: Run `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
- frontend: Not required; frontend is frozen and must not be touched.
- observability: Run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` after the backend commands. If needed, also inspect the relevant JSONL log directly and record the current-run trace_id/request_id/report_id plus module/function/block fields. Do not run or claim W02 canonical today-week closeout.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if the rework changes backend business semantics.
- Reject if the rework widens into frontend, report_workflow, DB/model changes, or unrelated active-slice modules.
- Reject if packet-local evidence is still stale or not attributable to the current verifier run.
- Reject if W01 is treated as owning canonical today-week closeout.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET

## Notes
- Planner is not required because packet topology and decomposition do not change.
- User escalation is not required because the blocker is evidentiary and local to W01 packet-local verification.
- Use bounded_fresh because the blocker spans evidence freshness and packet-local observability artifacts, not a tiny in-context correction.
- W02 remains responsible for wave_final canonical today-week verification.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
  "feature_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Packet-Local Evidence Freshness Rework",
  "summary": "Issue a bounded fresh coder rework to make W01 packet-local read-only observability evidence attributable to the current verifier run. Backend behavior is already green; the rework must produce or expose fresh packet-local trace_id/request_id/report_id evidence for the exercised backend active-slice flow without claiming canonical today-week closeout.",
  "write_scope": [
    "/opt/astro-project/backend/app/services/week_brief_service.py",
    "/opt/astro-project/tests/test_week_brief_service.py",
    "/opt/astro-project/tests/test_week_brief_api.py",
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET.md"
  ],
  "inputs": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT",
    "/opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json",
    "/opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md",
    "Reviewer blocker: backend quick and targeted pytest passed, but read-only observability evidence was stale and lacked current-run trace_id/request_id/report_id attribution."
  ],
  "acceptance_criteria": [
    "Diff remains inside the declared write scope.",
    "WeekBrief payload, envelope, fallback, API, Day/Week business semantics, and scoring behavior remain unchanged.",
    "Targeted WeekBrief tests and backend quick remain green.",
    "A current verifier run can produce or identify fresh packet-local evidence with stable module/function/block attribution and current trace_id/request_id/report_id values.",
    "The packet keeps W01 observability ownership as packet_local and does not require or claim canonical today-week closeout."
  ],
  "verification_profile": {
    "backend": "Run `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.",
    "frontend": "Not required; frontend is frozen and must not be touched.",
    "observability": "Run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` after the backend commands. If needed, also inspect the relevant JSONL log directly and record the current-run trace_id/request_id/report_id plus module/function/block fields. Do not run or claim W02 canonical today-week closeout."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Reject if the rework changes backend business semantics.",
    "Reject if the rework widens into frontend, report_workflow, DB/model changes, or unrelated active-slice modules.",
    "Reject if packet-local evidence is still stale or not attributable to the current verifier run.",
    "Reject if W01 is treated as owning canonical today-week closeout."
  ],
  "dependencies": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET"
  ],
  "notes": [
    "Planner is not required because packet topology and decomposition do not change.",
    "User escalation is not required because the blocker is evidentiary and local to W01 packet-local verification.",
    "Use bounded_fresh because the blocker spans evidence freshness and packet-local observability artifacts, not a tiny in-context correction.",
    "W02 remains responsible for wave_final canonical today-week verification."
  ],
  "parent_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
