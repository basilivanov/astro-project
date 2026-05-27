# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY`

## Summary
Extract Week seed bundle assembly, Week day normalization, Week summary normalization, and any Week-owned chunk/block parsing needed by WeekBrief assembly into a Week-owned helper module, then rewire WeekBrief service and report workflow prompt-context usage to that boundary.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/week_brief_seed.py
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/backend/app/services/report_workflow.py
- /opt/astro-project/tests/test_week_brief_service.py
- /opt/astro-project/tests/test_week_brief_api.py

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/docs/week-legacy-boundary-refactor/architect_manifest.json
- /opt/astro-project/docs/week-legacy-boundary-refactor/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/week-legacy-boundary-refactor/EXECUTION_PACKET.md
- /opt/astro-project/docs/week-legacy-boundary-refactor/requirements.slice.week-legacy-boundary-refactor.xml
- /opt/astro-project/docs/week-legacy-boundary-refactor/development-plan.slice.week-legacy-boundary-refactor.xml

## Acceptance Criteria
- backend/app/services/week_brief_seed.py exists as the Week-owned source for Week seed bundle assembly and Week normalization helpers used by WeekBrief assembly.
- backend/app/services/week_brief_service.py imports Week seed and normalization helpers from backend/app/services/week_brief_seed.py, not from private report_workflow.py helpers.
- backend/app/services/report_workflow.py remains present and continues to own report orchestration while delegating Week seed normalization through the Week-owned helper where required.
- Week prompt-context preparation remains functional and covered by targeted backend tests.
- No changes are made to backend/app/main.py, backend/app/services/week_map.py, backend/app/services/day_brief*, Week scoring semantics, day/week/natal payload contracts, or long-form report contour.
- Backend tests cover stable fallback behavior when Week seed data is partial or chunk parsing degrades.

## Verification Profile
- backend: Run backend quick plus targeted WeekBrief service/API tests after the backend boundary change; if a 500 or crash appears, add or update a reproducing test before claiming green.
- frontend: Not required for this backend-only packet.
- observability: Coder should record local test evidence only; canonical Today/Week runtime evidence is not owned by this packet.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - test-results/**/*
    - .task-logs/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays within the packet write scope and architect frozen scope is untouched.
- No direct private-helper dependency from week_brief_service.py to report_workflow.py remains for Week seed or Week normalization helpers.
- WeekBrief fallback, telemetry, prompt-context behavior, and payload semantics are demonstrably stable through the targeted backend tests.
- report_workflow.py is not deleted or broadly decomposed beyond the Week seed boundary required by the slice.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING

## Notes
- This packet owns the highest rework-risk backend seam and must land before frontend compatibility work depends on stable backend payload expectations.
- Do not rewrite backend/app/services/week_map.py in this feature.
- Do not fully decompose backend/app/main.py or backend/app/services/report_workflow.py in this feature.
