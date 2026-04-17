# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN

## Title
Week Boundary Rerun

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`

## Packet Type
execution

## Summary
Tighten or confirm the frontend Week boundary so canonical `/week` maps only canonical `week_brief`, legacy-only inputs fail closed honestly, and compatibility reconstruction remains explicit and isolated.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN`

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
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/**

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W00-ARCHITECT-FORMALIZATION
- feature brief
- execution packet
- architect manifest
- current `/week` route and Week helper baseline

## Acceptance Criteria
- Canonical `/week` uses only `week_brief` or `week_brief_envelope.data` to build the product surface.
- If a completed Week report returns only `week_map`, chunks, or raw legacy fields, `/week` renders the empty/create state and no Week product surface.
- Compatibility reconstruction remains in `frontend/lib/week-brief-compat.ts` and is not imported by the canonical `/week` route.
- Canonical Week navigation and primary CTA still point to the concrete report when canonical payload exists.
- In-progress Week state remains top-layer only and does not expose completed domain, day, action, or deep-section stacks.
- No backend, Create, Home, Read, Billing, Telegram hook, or root GRACE canon files are modified.

## Verification Profile
- backend: not required unless backend files are unexpectedly touched; if touched, stop and escalate before implementation
- frontend: python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts when route or visual state changes
- observability: packet_local only; no canonical Today/Week closeout is owned here, and degraded-but-expected is acceptable when no fresh canonical emitter evidence exists

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Diff stays inside write scope and frozen scope remains untouched.
- `/week` does not import or call the legacy compatibility mapper.
- User-visible Week UI does not leak raw internal tokens: `legacy`, `fallback`, `week_map`, `weekbrief`, `compatibility`, `headline`, `markdown`, or `weekly report`.
- Tests prove canonical continuity, fail-closed legacy-only behavior, and compatibility isolation.

## Dependencies
-

## Notes
- This is the only planned implementation packet for W01.
- If the current code already satisfies the contract, tighten only stale tests or evidence hooks needed by verifier.
- Planner stays off unless the slice can no longer remain bounded.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Week Boundary Rerun",
  "summary": "Tighten or confirm the frontend Week boundary so canonical `/week` maps only canonical `week_brief`, legacy-only inputs fail closed honestly, and compatibility reconstruction remains explicit and isolated.",
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
    "/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/**"
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "execution packet",
    "architect manifest",
    "current `/week` route and Week helper baseline"
  ],
  "acceptance_criteria": [
    "Canonical `/week` uses only `week_brief` or `week_brief_envelope.data` to build the product surface.",
    "If a completed Week report returns only `week_map`, chunks, or raw legacy fields, `/week` renders the empty/create state and no Week product surface.",
    "Compatibility reconstruction remains in `frontend/lib/week-brief-compat.ts` and is not imported by the canonical `/week` route.",
    "Canonical Week navigation and primary CTA still point to the concrete report when canonical payload exists.",
    "In-progress Week state remains top-layer only and does not expose completed domain, day, action, or deep-section stacks.",
    "No backend, Create, Home, Read, Billing, Telegram hook, or root GRACE canon files are modified."
  ],
  "verification_profile": {
    "backend": "not required unless backend files are unexpectedly touched; if touched, stop and escalate before implementation",
    "frontend": "python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts when route or visual state changes",
    "observability": "packet_local only; no canonical Today/Week closeout is owned here, and degraded-but-expected is acceptable when no fresh canonical emitter evidence exists"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Diff stays inside write scope and frozen scope remains untouched.",
    "`/week` does not import or call the legacy compatibility mapper.",
    "User-visible Week UI does not leak raw internal tokens: `legacy`, `fallback`, `week_map`, `weekbrief`, `compatibility`, `headline`, `markdown`, or `weekly report`.",
    "Tests prove canonical continuity, fail-closed legacy-only behavior, and compatibility isolation."
  ],
  "dependencies": [],
  "notes": [
    "This is the only planned implementation packet for W01.",
    "If the current code already satisfies the contract, tighten only stale tests or evidence hooks needed by verifier.",
    "Planner stays off unless the slice can no longer remain bounded."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
