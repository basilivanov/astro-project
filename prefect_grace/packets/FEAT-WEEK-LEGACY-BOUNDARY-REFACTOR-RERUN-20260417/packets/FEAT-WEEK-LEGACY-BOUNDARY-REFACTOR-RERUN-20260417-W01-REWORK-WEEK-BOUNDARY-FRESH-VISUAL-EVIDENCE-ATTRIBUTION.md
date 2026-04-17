# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-FRESH-VISUAL-EVIDENCE-ATTRIBUTION

## Title
Rework Week Boundary Fresh Visual Evidence Attribution

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-FRESH-VISUAL-EVIDENCE-ATTRIBUTION`

## Packet Type
rework

## Summary
Repair the remaining W01 evidence-only blocker by making the verifier-run Week Playwright lane emit and attribute fresh successful visual proof for both canonical and fail-closed Week states. Do not reopen the already-resolved product boundary work unless a narrow evidence-production fix proves unavoidable.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Write Scope
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts
- /opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417/**
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/**

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`
- Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`
- Latest verifier evidence for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-VERIFIER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`
- Current failing/old artifact references under `/opt/astro-project/frontend/test-results/` and the feature-local evidence directory

## Acceptance Criteria
- Fresh successful visual proof exists for both canonical Week and fail-closed Week states and is attributable to the current rerun, not to earlier or failed runs.
- The artifact-producing Playwright lane used by verifier emits stable screenshot or attachment outputs for both targeted Week scenarios.
- If any evidence handoff file or artifact index is used, it references only the current successful rerun outputs.
- No unrelated product, backend, or GRACE canon changes are introduced.

## Verification Profile
- backend: none
- frontend: Rerun the artifact-producing targeted Playwright lane for `e2e/week-page-fallback.spec.ts` and `e2e/canonical-week-continuity.spec.ts`, and confirm fresh successful screenshot/attachment files exist for both scenarios; rerun `corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts` only if any non-e2e frontend file is touched
- observability: not required for evidence-only rework; if any runtime/product file is changed, repeat `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` and keep the verdict `clean` or `degraded-but-expected`

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if visual artifacts still come from earlier or failed runs.
- Reject if both canonical and fail-closed Week states are not covered by fresh attributable success artifacts.
- Reject if the rework widens back into product-boundary changes without a direct evidence-production need.
- Reject if evidence attribution remains implicit or unverifiable from the current rerun outputs.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE

## Notes
- This is a pipeline/evidence repair packet, not another product-behavior rework.
- Keep the scope on Playwright artifact emission, naming, attachment capture, export location, and evidence handoff only.
- Planner is not required because packet topology does not need to change.
- User escalation is not required because no business decision is missing.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-FRESH-VISUAL-EVIDENCE-ATTRIBUTION",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Rework Week Boundary Fresh Visual Evidence Attribution",
  "summary": "Repair the remaining W01 evidence-only blocker by making the verifier-run Week Playwright lane emit and attribute fresh successful visual proof for both canonical and fail-closed Week states. Do not reopen the already-resolved product boundary work unless a narrow evidence-production fix proves unavoidable.",
  "write_scope": [
    "/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts",
    "/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts",
    "/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417/**",
    "/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/**"
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`",
    "Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`",
    "Latest verifier evidence for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-VERIFIER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`",
    "Current failing/old artifact references under `/opt/astro-project/frontend/test-results/` and the feature-local evidence directory"
  ],
  "acceptance_criteria": [
    "Fresh successful visual proof exists for both canonical Week and fail-closed Week states and is attributable to the current rerun, not to earlier or failed runs.",
    "The artifact-producing Playwright lane used by verifier emits stable screenshot or attachment outputs for both targeted Week scenarios.",
    "If any evidence handoff file or artifact index is used, it references only the current successful rerun outputs.",
    "No unrelated product, backend, or GRACE canon changes are introduced."
  ],
  "verification_profile": {
    "backend": "none",
    "frontend": "Rerun the artifact-producing targeted Playwright lane for `e2e/week-page-fallback.spec.ts` and `e2e/canonical-week-continuity.spec.ts`, and confirm fresh successful screenshot/attachment files exist for both scenarios; rerun `corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts` only if any non-e2e frontend file is touched",
    "observability": "not required for evidence-only rework; if any runtime/product file is changed, repeat `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` and keep the verdict `clean` or `degraded-but-expected`"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Reject if visual artifacts still come from earlier or failed runs.",
    "Reject if both canonical and fail-closed Week states are not covered by fresh attributable success artifacts.",
    "Reject if the rework widens back into product-boundary changes without a direct evidence-production need.",
    "Reject if evidence attribution remains implicit or unverifiable from the current rerun outputs."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE"
  ],
  "notes": [
    "This is a pipeline/evidence repair packet, not another product-behavior rework.",
    "Keep the scope on Playwright artifact emission, naming, attachment capture, export location, and evidence handoff only.",
    "Planner is not required because packet topology does not need to change.",
    "User escalation is not required because no business decision is missing."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
