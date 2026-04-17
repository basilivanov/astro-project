# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-VERIFIER-WEEK-BOUNDARY-EVIDENCE

## Title
Week Boundary Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-VERIFIER-WEEK-BOUNDARY-EVIDENCE`

## Packet Type
execution

## Summary
Produce fresh targeted Week unit, helper, E2E, visual, and packet-local/read-only observability evidence for the W01 rerun.

## Wave
W01

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/evidence/**
- /opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417/**

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/EXECUTION_PACKET.md
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/architect_manifest.json

## Acceptance Criteria
- All targeted commands are executed and recorded with PASS/FAIL status.
- Evidence covers canonical Week continuity and fail-closed legacy-only empty state.
- Visual proof includes fresh canonical Week surface and fail-closed empty-state captures or Playwright attachments.
- Console/page-error hygiene is recorded for the targeted Playwright flows.
- Read-only observability review is recorded as `clean` or `degraded-but-expected`; `unexpected-degradation` and `no-evidence-blocker` block acceptance.
- Evidence explicitly states that canonical Today/Week runtime closeout is not owned by this wave because no canonical emitter command is intentionally required.

## Verification Profile
- backend: not required for this frontend-only wave; if backend drift is detected, block and route back because it is outside scope.
- frontend: `python3 -m pytest -q tests/test_week_brief_frontend_mapping.py`; `corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts`; `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts`
- observability: `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`; observability_scope=`packet_local`; canonical_flow_commands=[]

## Execution Hints
- workdir: /opt/astro-project
- Store the verification report under `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/evidence/`.
- If a page crash or 500 appears, block verification and require a reproduction test before rerunning.

## Reviewer Gate
- Reject if any required command is skipped without explicit blocker.
- Reject if visual proof does not show both canonical and fail-closed states.
- Reject if observability is missing, fragmented, `unexpected-degradation`, or `no-evidence-blocker`.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN

## Notes
- Fresh Today/Week canonical evidence is not required here; packet-local/read-only evidence is the owned observability surface.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-VERIFIER-WEEK-BOUNDARY-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Week Boundary Evidence",
  "summary": "Produce fresh targeted Week unit, helper, E2E, visual, and packet-local/read-only observability evidence for the W01 rerun.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/evidence/**",
    "/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417/**"
  ],
  "verification_profile": {
    "backend": "not required for this frontend-only wave; block if backend drift appears",
    "frontend": "python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; observability_scope=packet_local; degraded-but-expected allowed"
  },
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN"
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN"
}
END_FINAL_PACKET_CONTRACT_JSON
