# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FRONTEND-WEEK-COMPATIBILITY-SPLIT`

## Summary
Split canonical Week mapping from legacy compatibility reconstruction so frontend/lib/week-brief.ts remains canonical-only and frontend/lib/week-brief-compat.ts owns legacy week_map plus chunks reconstruction for secondary compatibility surfaces only.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/lib/week-brief.ts
- /opt/astro-project/frontend/lib/week-brief-compat.ts
- /opt/astro-project/tests/test_week_brief_frontend_mapping.py
- /opt/astro-project/frontend/test/lib/week-brief.test.ts

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- /opt/astro-project/docs/week-legacy-boundary-refactor/architect_manifest.json
- /opt/astro-project/docs/week-legacy-boundary-refactor/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/week-legacy-boundary-refactor/requirements.slice.week-legacy-boundary-refactor.xml
- /opt/astro-project/docs/week-legacy-boundary-refactor/development-plan.slice.week-legacy-boundary-refactor.xml

## Acceptance Criteria
- Canonical Week mapping remains in frontend/lib/week-brief.ts and accepts canonical week_brief only.
- Non-canonical legacy week_map or chunks reconstruction is moved to frontend/lib/week-brief-compat.ts.
- The canonical /week product path remains fail-closed for non-canonical inputs.
- No visible Week layout files, frontend/app/week/page.tsx, frontend/components/week/**, or frontend/app/read/** are changed.
- Frontend helper tests cover canonical-only mapping and explicit compatibility reconstruction isolation.

## Verification Profile
- backend: Not required for this frontend-helper packet.
- frontend: Run targeted Python and Jest frontend mapping/helper tests; visual proof is not required because visible UI files must not be touched.
- observability: Coder should record local test evidence only; canonical Today/Week runtime evidence is not owned by this packet.
- execution:
  - backend_commands:
  - frontend_commands:
    - python3 -m pytest -q tests/test_week_brief_frontend_mapping.py
    - corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: False
  - artifact_globs:
    - frontend/test-results/**/*
    - test-results/**/*
    - .task-logs/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays within the packet write scope and frozen visible Week UI scope is untouched.
- Canonical Week mapping does not import or depend on legacy compatibility reconstruction.
- Compatibility reconstruction is explicit and isolated in frontend/lib/week-brief-compat.ts.
- Targeted frontend mapping/helper tests prove fail-closed canonical behavior and compatibility isolation.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY

## Notes
- If implementation discovers that visible Week UI import rewiring is absolutely required, stop and route to architect before widening scope because the architect frozen scope excludes visible Week UI files.
