# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN

## Title
Week Boundary Rerun

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Packet Type
execution

## Summary
Confirm or tighten the /week boundary so only canonical week_brief drives the product surface, legacy-only inputs fail closed, and rerun-B evidence hooks stay explicit.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Write Scope
- /opt/astro-project/frontend/app/week/page.tsx
- /opt/astro-project/frontend/components/week/**
- /opt/astro-project/frontend/lib/week-brief.ts
- /opt/astro-project/frontend/lib/week-brief-compat.ts
- /opt/astro-project/frontend/test/app/week-page.test.tsx
- /opt/astro-project/frontend/test/lib/week-brief.test.ts
- /opt/astro-project/tests/test_week_brief_frontend_mapping.py
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts
- /opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W00-ARCHITECT-FORMALIZATION
- feature brief
- execution packet
- architect manifest
- current /week route and Week helper baseline

## Acceptance Criteria
- Canonical /week uses only week_brief or week_brief_envelope.data to build the product surface.
- Completed Week reports with only legacy payload render the empty/create state and no Week product surface.
- Compatibility reconstruction remains in frontend/lib/week-brief-compat.ts and is not imported by the canonical /week route.
- If Playwright evidence harnesses are touched, rerun-B packet IDs and evidence paths are refreshed.
- No backend, Create, Home, Read, Billing, Telegram hook, runtime-indicator specs, or root GRACE canon files are modified.

## Verification Profile
- backend: not required unless unexpected backend drift appears; if it does, stop and escalate
- frontend: python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts when route or evidence harness changes
- observability: packet_local only; no canonical Today/Week closeout is owned here, and degraded-but-expected is acceptable when no canonical emitter trace is intentionally produced

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Diff stays inside write scope and frozen scope remains untouched.
- /week does not import or call the legacy compatibility mapper.
- User-visible Week UI does not leak raw internal tokens.
- Tests or evidence hooks prove canonical continuity, fail-closed legacy-only behavior, and rerun-B evidence attribution.

## Dependencies
-

## Notes
- This is the only planned implementation packet for W01.
- If the current code already satisfies the contract, limit changes to stale tests or evidence harnesses needed by verifier.
- Planner stays off unless the slice can no longer remain bounded.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Week Boundary Rerun",
  "summary": "Confirm or tighten the /week boundary so only canonical week_brief drives the product surface, legacy-only inputs fail closed, and rerun-B evidence hooks stay explicit.",
  "write_scope": [
    "/opt/astro-project/frontend/app/week/page.tsx",
    "/opt/astro-project/frontend/components/week/**",
    "/opt/astro-project/frontend/lib/week-brief.ts",
    "/opt/astro-project/frontend/lib/week-brief-compat.ts",
    "/opt/astro-project/frontend/test/app/week-page.test.tsx",
    "/opt/astro-project/frontend/test/lib/week-brief.test.ts",
    "/opt/astro-project/tests/test_week_brief_frontend_mapping.py",
    "/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts",
    "/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts",
    "/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**"
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "execution packet",
    "architect manifest",
    "current /week route and Week helper baseline"
  ],
  "acceptance_criteria": [
    "Canonical /week uses only week_brief or week_brief_envelope.data to build the product surface.",
    "Completed Week reports with only legacy payload render the empty/create state and no Week product surface.",
    "Compatibility reconstruction remains in frontend/lib/week-brief-compat.ts and is not imported by the canonical /week route.",
    "If Playwright evidence harnesses are touched, rerun-B packet IDs and evidence paths are refreshed.",
    "No backend, Create, Home, Read, Billing, Telegram hook, runtime-indicator specs, or root GRACE canon files are modified."
  ],
  "verification_profile": {
    "backend": "not required unless unexpected backend drift appears; if it does, stop and escalate",
    "frontend": "python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts when route or evidence harness changes",
    "observability": "packet_local only; no canonical Today/Week closeout is owned here, and degraded-but-expected is acceptable when no canonical emitter trace is intentionally produced"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Diff stays inside write scope and frozen scope remains untouched.",
    "/week does not import or call the legacy compatibility mapper.",
    "User-visible Week UI does not leak raw internal tokens.",
    "Tests or evidence hooks prove canonical continuity, fail-closed legacy-only behavior, and rerun-B evidence attribution."
  ],
  "dependencies": [],
  "notes": [
    "This is the only planned implementation packet for W01.",
    "If the current code already satisfies the contract, limit changes to stale tests or evidence harnesses needed by verifier.",
    "Planner stays off unless the slice can no longer remain bounded."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
