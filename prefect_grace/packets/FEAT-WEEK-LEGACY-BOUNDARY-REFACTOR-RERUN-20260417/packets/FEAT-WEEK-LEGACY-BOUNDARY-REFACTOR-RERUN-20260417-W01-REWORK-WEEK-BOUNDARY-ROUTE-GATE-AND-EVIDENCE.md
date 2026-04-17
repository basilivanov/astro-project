# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE

## Title
Rework Week Boundary Route Gate And Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Packet Type
rework

## Summary
Resolve the local W01 blockers by restoring the targeted Week route-gate Jest lane, making the legacy-only `/week` fail-closed scenario deterministic again, removing the canonical Playwright console-hygiene failure without broad suppression, and producing fresh passing visual proof for both canonical and fail-closed Week states.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx
- /opt/astro-project/frontend/app/week/page.tsx
- /opt/astro-project/frontend/lib/week-brief.ts
- /opt/astro-project/frontend/lib/week-brief-compat.ts
- /opt/astro-project/frontend/test/app/week-page.test.tsx
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`
- Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-VERDICT`
- Verifier evidence `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/evidence/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-EVIDENCE.verification.md`
- Failing canonical Playwright artifacts under `/opt/astro-project/frontend/test-results/verifier-week-boundary-20260417-20260417/canonical-week-continuity--57de0-thout-brittle-copy-coupling/`
- Failing fail-closed Playwright artifacts under `/opt/astro-project/frontend/test-results/verifier-week-boundary-20260417-20260417/week-page-fallback-Week-Pa-22ebc-y-week-chunks-are-available/`

## Acceptance Criteria
- The shared runtime badge route gate no longer breaks the targeted Week Jest route-gate assertion and preserves existing day-home behavior.
- The legacy-only `/week` scenario renders the approved honest empty/create state and the targeted fail-closed assertion passes.
- Canonical continuity Playwright completes without unexpected console or pageerror noise; if an exact Next dev RSC message is proven to be benign navigation noise, it is handled narrowly and documented rather than broadly suppressed.
- Fresh passing visual proof exists for both canonical and fail-closed Week states.
- No backend, root GRACE, or unrelated product-surface changes are introduced.

## Verification Profile
- backend: none
- frontend: corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts; if `frontend/lib/week-brief.ts` or `frontend/lib/week-brief-compat.ts` changes, also run python3 -m pytest -q tests/test_week_brief_frontend_mapping.py
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; keep packet-local verdict at `clean` or `degraded-but-expected`

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject if the fix broadens shared route-gate behavior beyond the minimal `/week` eligibility change.
- Reject if fail-closed behavior is weakened or if the canonical `/week` route begins depending on compatibility reconstruction.
- Reject if fresh passing visual proof for both canonical and fail-closed states is still missing.
- Reject if console hygiene is achieved by broad error suppression instead of a bounded flow fix or a narrow proven-benign filter.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN

## Notes
- This remains a frontend-local rework inside the existing wave; planner is not needed.
- Shared route-gate code lives in `frontend/app/layout.tsx`; touching it is allowed only to make `/week` eligible without regressing the existing day-only mapping.
- Prefer fixing the actual source of canonical console noise; only an exact, proven non-product dev-navigation message may be filtered narrowly in the test harness.
- Do not widen into runtime-indicator feature work, backend changes, or new Week product semantics.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Rework Week Boundary Route Gate And Evidence",
  "summary": "Resolve the local W01 blockers by restoring the targeted Week route-gate Jest lane, making the legacy-only `/week` fail-closed scenario deterministic again, removing the canonical Playwright console-hygiene failure without broad suppression, and producing fresh passing visual proof for both canonical and fail-closed Week states.",
  "write_scope": [
    "/opt/astro-project/frontend/app/layout.tsx",
    "/opt/astro-project/frontend/app/week/page.tsx",
    "/opt/astro-project/frontend/lib/week-brief.ts",
    "/opt/astro-project/frontend/lib/week-brief-compat.ts",
    "/opt/astro-project/frontend/test/app/week-page.test.tsx",
    "/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts",
    "/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts"
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`",
    "Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-VERDICT`",
    "Verifier evidence `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/evidence/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-EVIDENCE.verification.md`",
    "Failing canonical Playwright artifacts under `/opt/astro-project/frontend/test-results/verifier-week-boundary-20260417-20260417/canonical-week-continuity--57de0-thout-brittle-copy-coupling/`",
    "Failing fail-closed Playwright artifacts under `/opt/astro-project/frontend/test-results/verifier-week-boundary-20260417-20260417/week-page-fallback-Week-Pa-22ebc-y-week-chunks-are-available/`"
  ],
  "acceptance_criteria": [
    "The shared runtime badge route gate no longer breaks the targeted Week Jest route-gate assertion and preserves existing day-home behavior.",
    "The legacy-only `/week` scenario renders the approved honest empty/create state and the targeted fail-closed assertion passes.",
    "Canonical continuity Playwright completes without unexpected console or pageerror noise; if an exact Next dev RSC message is proven to be benign navigation noise, it is handled narrowly and documented rather than broadly suppressed.",
    "Fresh passing visual proof exists for both canonical and fail-closed Week states.",
    "No backend, root GRACE, or unrelated product-surface changes are introduced."
  ],
  "verification_profile": {
    "backend": "none",
    "frontend": "corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts; if `frontend/lib/week-brief.ts` or `frontend/lib/week-brief-compat.ts` changes, also run python3 -m pytest -q tests/test_week_brief_frontend_mapping.py",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; keep packet-local verdict at `clean` or `degraded-but-expected`"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Reject if the fix broadens shared route-gate behavior beyond the minimal `/week` eligibility change.",
    "Reject if fail-closed behavior is weakened or if the canonical `/week` route begins depending on compatibility reconstruction.",
    "Reject if fresh passing visual proof for both canonical and fail-closed states is still missing.",
    "Reject if console hygiene is achieved by broad error suppression instead of a bounded flow fix or a narrow proven-benign filter."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN"
  ],
  "notes": [
    "This remains a frontend-local rework inside the existing wave; planner is not needed.",
    "Shared route-gate code lives in `frontend/app/layout.tsx`; touching it is allowed only to make `/week` eligible without regressing the existing day-only mapping.",
    "Prefer fixing the actual source of canonical console noise; only an exact, proven non-product dev-navigation message may be filtered narrowly in the test harness.",
    "Do not widen into runtime-indicator feature work, backend changes, or new Week product semantics."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
