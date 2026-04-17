# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Title
Fix Week Legacy Raw-Slug Fallback Guard

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD`

## Packet Type
rework

## Summary
Resume the coder packet to fix the localized failure in `week-page-fallback.spec.ts` for the raw-slug legacy fallback guard. The fix must preserve the canonical `/week` boundary: legacy-only payloads, including raw slug chunk/title data, must fail closed to the empty/create state without rendering a Week product surface or leaking internal tokens.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Write Scope
- /opt/astro-project/frontend/app/week/page.tsx
- /opt/astro-project/frontend/lib/week-brief.ts
- /opt/astro-project/frontend/lib/week-brief-compat.ts
- /opt/astro-project/frontend/test/app/week-page.test.tsx
- /opt/astro-project/frontend/test/lib/week-brief.test.ts
- /opt/astro-project/tests/test_week_brief_frontend_mapping.py
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B/evidence/**

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`.
- Reviewer verdict `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT`.
- Reviewer blocker: required Playwright verification failed for the raw-slug legacy fallback guard.
- Latest verifier evidence: visual proof and packet-local observability are sufficient, but legacy-only boundary evidence remains incomplete until `week-page-fallback.spec.ts` passes.

## Acceptance Criteria
- The raw-slug legacy fallback Playwright scenario passes without weakening the canonical `/week` boundary.
- Completed Week reports containing only legacy payload, raw slug titles/sections, chunks, or `week_map` render the empty/create state and no Week product surface.
- `/week` still does not import or call `frontend/lib/week-brief-compat.ts`, `mapLegacyWeekMigrationToSurface`, or `hasExplicitWeekMigrationPayload`.
- User-visible `/week` output does not leak raw internal tokens: `legacy`, `fallback`, `week_map`, `weekbrief`, `compatibility`, `headline`, `markdown`, or `weekly report`.
- No backend, Create, Home, Read, Billing, Telegram hook, runtime-indicator specs, or root GRACE canon files are modified.
- Fresh rerun-B evidence is updated only for the targeted failed flow if the Playwright harness regenerates artifacts.

## Verification Profile
- backend: not required; if backend files are touched or backend drift is detected, stop and escalate because backend is frozen for this wave
- frontend: ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts -g "should keep legacy raw slug fallback data out of the canonical week route"; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts; run `python3 -m pytest -q tests/test_week_brief_frontend_mapping.py` or targeted Jest only if mapper/route code changes
- observability: packet_local only; preserve the existing sufficient observability posture, and if new evidence is generated record verdict as `clean` or `degraded-but-expected`, not `unexpected-degradation` or `no-evidence-blocker`

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to at most two small blocker reasons

## Reviewer Gate
- Reject if the fix makes `/week` consume the legacy compatibility mapper.
- Reject if the raw-slug scenario passes by loosening assertions instead of preserving fail-closed behavior.
- Reject if visual/evidence artifacts are missing or stale after rerunning the failing Playwright scenario.
- Reject any silent scope expansion into frozen backend, Day/Home, runtime-indicator, or root GRACE canon files.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN

## Notes
- This is localized product/test rework, not a planner or user-decision blocker.
- Keep the fix limited to the failing legacy-only boundary path and adjacent tests/evidence.
- Do not re-formalize the feature or change the W01 packet topology.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Fix Week Legacy Raw-Slug Fallback Guard",
  "summary": "Resume the coder packet to fix the localized failure in `week-page-fallback.spec.ts` for the raw-slug legacy fallback guard. The fix must preserve the canonical `/week` boundary: legacy-only payloads, including raw slug chunk/title data, must fail closed to the empty/create state without rendering a Week product surface or leaking internal tokens.",
  "write_scope": [
    "/opt/astro-project/frontend/app/week/page.tsx",
    "/opt/astro-project/frontend/lib/week-brief.ts",
    "/opt/astro-project/frontend/lib/week-brief-compat.ts",
    "/opt/astro-project/frontend/test/app/week-page.test.tsx",
    "/opt/astro-project/frontend/test/lib/week-brief.test.ts",
    "/opt/astro-project/tests/test_week_brief_frontend_mapping.py",
    "/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts",
    "/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**",
    "/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B/evidence/**"
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`.",
    "Reviewer verdict `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT`.",
    "Reviewer blocker: required Playwright verification failed for the raw-slug legacy fallback guard.",
    "Latest verifier evidence: visual proof and packet-local observability are sufficient, but legacy-only boundary evidence remains incomplete until `week-page-fallback.spec.ts` passes."
  ],
  "acceptance_criteria": [
    "The raw-slug legacy fallback Playwright scenario passes without weakening the canonical `/week` boundary.",
    "Completed Week reports containing only legacy payload, raw slug titles/sections, chunks, or `week_map` render the empty/create state and no Week product surface.",
    "`/week` still does not import or call `frontend/lib/week-brief-compat.ts`, `mapLegacyWeekMigrationToSurface`, or `hasExplicitWeekMigrationPayload`.",
    "User-visible `/week` output does not leak raw internal tokens: `legacy`, `fallback`, `week_map`, `weekbrief`, `compatibility`, `headline`, `markdown`, or `weekly report`.",
    "No backend, Create, Home, Read, Billing, Telegram hook, runtime-indicator specs, or root GRACE canon files are modified.",
    "Fresh rerun-B evidence is updated only for the targeted failed flow if the Playwright harness regenerates artifacts."
  ],
  "verification_profile": {
    "backend": "not required; if backend files are touched or backend drift is detected, stop and escalate because backend is frozen for this wave",
    "frontend": "./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts -g \"should keep legacy raw slug fallback data out of the canonical week route\"; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts; run `python3 -m pytest -q tests/test_week_brief_frontend_mapping.py` or targeted Jest only if mapper/route code changes",
    "observability": "packet_local only; preserve the existing sufficient observability posture, and if new evidence is generated record verdict as `clean` or `degraded-but-expected`, not `unexpected-degradation` or `no-evidence-blocker`"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to at most two small blocker reasons"
  },
  "reviewer_gate": [
    "Reject if the fix makes `/week` consume the legacy compatibility mapper.",
    "Reject if the raw-slug scenario passes by loosening assertions instead of preserving fail-closed behavior.",
    "Reject if visual/evidence artifacts are missing or stale after rerunning the failing Playwright scenario.",
    "Reject any silent scope expansion into frozen backend, Day/Home, runtime-indicator, or root GRACE canon files."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN"
  ],
  "notes": [
    "This is localized product/test rework, not a planner or user-decision blocker.",
    "Keep the fix limited to the failing legacy-only boundary path and adjacent tests/evidence.",
    "Do not re-formalize the feature or change the W01 packet topology."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
