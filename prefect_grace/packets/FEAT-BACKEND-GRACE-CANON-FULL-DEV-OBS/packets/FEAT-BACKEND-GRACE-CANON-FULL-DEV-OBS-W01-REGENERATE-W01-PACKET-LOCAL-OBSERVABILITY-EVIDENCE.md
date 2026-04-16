# Packet: FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## Title
Regenerate W01 Packet-Local Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01:packet:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE`

## Packet Type
rework

## Summary
Resolve the W01 reviewer blocker by producing fresh packet-local observability evidence after the already-passing backend verification profile, and apply only minimal targeted fixes if the current emitted evidence still lacks reconstructable trace identifiers.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
`FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/evidence
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/reviews
- /opt/astro-project/backend/app/main.py
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/backend/app/middleware/correlation.py
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/backend/app/services/day_brief_validators.py
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/backend/app/services/analytics.py
- /opt/astro-project/tests/test_day_brief.py
- /opt/astro-project/tests/test_day_brief_schema.py
- /opt/astro-project/tests/test_week_brief_service.py
- /opt/astro-project/tests/test_week_brief_api.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tests/test_catalog_logging.py
- /opt/astro-project/tests/test_billing_scheduler.py

## Inputs
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-EVIDENCE
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REVIEWER-VERDICT
- /opt/astro-project/docs/backend-grace-canon-full-dev-observability/architect_manifest.json
- /opt/astro-project/docs/backend-grace-canon-full-dev-observability/verification-matrix.slice.backend-grace-canon-full-dev-observability.md

## Acceptance Criteria
- Fresh W01 evidence is generated after rerunning the required backend profile, not reused from stale pre-2026-04-16 artifacts.
- The evidence includes exact command lines, PASS/FAIL results, reviewed log or artifact paths, and latest relevant trace identifiers.
- Packet-local observability verdict is changed from no-evidence-blocker to clean or degraded-but-expected only if the emitted evidence is reconstructable by module, function or block, event, correlation_id, and trace_id where the path is exercised.
- If scheduler or analytics paths are not exercised by the packet-local commands, the evidence explicitly records that non-emission as degraded-but-expected rather than silently omitting it.
- If fresh emitted evidence still lacks required identifiers for exercised paths, apply the smallest code/test fix within the original W01 backend active-slice scope and rerun the required checks.
- No frontend files, report_workflow.py decomposition, business semantics, logging transport, or repo-wide cleanup are introduced.

## Verification Profile
- backend: Run `docker exec astro-project-backend-1 python3 scripts/pipeline.py` and the targeted pytest bundle: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py`.
- frontend: not required; no UI files are in scope.
- observability: Run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` immediately after the backend commands, then inspect the relevant structured logs/artifacts and record `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker` with trace_id/correlation_id/request_id/report_id details where available.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to at most two small blocker reasons

## Reviewer Gate
- Reject green-only evidence that lacks fresh post-test observability review.
- Reject stale artifacts or log samples that predate the rework verification run.
- Reject claims of clean observability if exercised paths lack trace_id or correlation_id attribution.
- Accept degraded-but-expected only when the non-emitted path was not exercised by the packet-local command profile and the evidence says so explicitly.
- Reject any scope expansion into frontend, report_workflow.py decomposition, new logging transport, or business-semantic changes.

## Dependencies
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET

## Notes
- Planner is not required because the blocker is local evidence reconstruction, not packet topology.
- Prefer evidence regeneration first; patch code only if fresh emitted evidence proves a real attribution gap remains.
- Keep packet.md as the primary execution contract and place any compact machine-readable result block at the tail of that packet if a packet file is materialized.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Regenerate W01 Packet-Local Observability Evidence",
  "summary": "Resolve the W01 reviewer blocker by producing fresh packet-local observability evidence after the already-passing backend verification profile, and apply only minimal targeted fixes if the current emitted evidence still lacks reconstructable trace identifiers.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/evidence",
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/reviews",
    "/opt/astro-project/backend/app/main.py",
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/backend/app/middleware/correlation.py",
    "/opt/astro-project/backend/app/services/day_brief.py",
    "/opt/astro-project/backend/app/services/day_brief_validators.py",
    "/opt/astro-project/backend/app/services/week_brief_service.py",
    "/opt/astro-project/backend/app/services/scheduler.py",
    "/opt/astro-project/backend/app/services/analytics.py",
    "/opt/astro-project/tests/test_day_brief.py",
    "/opt/astro-project/tests/test_day_brief_schema.py",
    "/opt/astro-project/tests/test_week_brief_service.py",
    "/opt/astro-project/tests/test_week_brief_api.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tests/test_catalog_logging.py",
    "/opt/astro-project/tests/test_billing_scheduler.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET",
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-EVIDENCE",
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REVIEWER-VERDICT",
    "/opt/astro-project/docs/backend-grace-canon-full-dev-observability/architect_manifest.json",
    "/opt/astro-project/docs/backend-grace-canon-full-dev-observability/verification-matrix.slice.backend-grace-canon-full-dev-observability.md"
  ],
  "acceptance_criteria": [
    "Fresh W01 evidence is generated after rerunning the required backend profile, not reused from stale pre-2026-04-16 artifacts.",
    "The evidence includes exact command lines, PASS/FAIL results, reviewed log or artifact paths, and latest relevant trace identifiers.",
    "Packet-local observability verdict is changed from no-evidence-blocker to clean or degraded-but-expected only if the emitted evidence is reconstructable by module, function or block, event, correlation_id, and trace_id where the path is exercised.",
    "If scheduler or analytics paths are not exercised by the packet-local commands, the evidence explicitly records that non-emission as degraded-but-expected rather than silently omitting it.",
    "If fresh emitted evidence still lacks required identifiers for exercised paths, apply the smallest code/test fix within the original W01 backend active-slice scope and rerun the required checks.",
    "No frontend files, report_workflow.py decomposition, business semantics, logging transport, or repo-wide cleanup are introduced."
  ],
  "verification_profile": {
    "backend": "Run `docker exec astro-project-backend-1 python3 scripts/pipeline.py` and the targeted pytest bundle: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py`.",
    "frontend": "not required; no UI files are in scope.",
    "observability": "Run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` immediately after the backend commands, then inspect the relevant structured logs/artifacts and record `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker` with trace_id/correlation_id/request_id/report_id details where available."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to at most two small blocker reasons"
  },
  "reviewer_gate": [
    "Reject green-only evidence that lacks fresh post-test observability review.",
    "Reject stale artifacts or log samples that predate the rework verification run.",
    "Reject claims of clean observability if exercised paths lack trace_id or correlation_id attribution.",
    "Accept degraded-but-expected only when the non-emitted path was not exercised by the packet-local command profile and the evidence says so explicitly.",
    "Reject any scope expansion into frontend, report_workflow.py decomposition, new logging transport, or business-semantic changes."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET"
  ],
  "notes": [
    "Planner is not required because the blocker is local evidence reconstruction, not packet topology.",
    "Prefer evidence regeneration first; patch code only if fresh emitted evidence proves a real attribution gap remains.",
    "Keep packet.md as the primary execution contract and place any compact machine-readable result block at the tail of that packet if a packet file is materialized."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
