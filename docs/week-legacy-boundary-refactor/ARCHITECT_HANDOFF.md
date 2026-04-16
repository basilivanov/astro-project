# Architect Handoff: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR

- Slice ID: `SLICE-FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- Slice dir: `/opt/astro-project/docs/week-legacy-boundary-refactor`
- Goal: Detach WeekBrief assembly from report_workflow private helpers and isolate frontend compatibility reconstruction without changing Week product semantics.
- Scope: Extract a Week-owned backend helper module for Week seed bundle assembly, Week day normalization, Week summary normalization, and any Week-owned chunk/block parsing needed by WeekBrief assembly.; Rewire WeekBrief assembly and Week prompt-context preparation to consume the Week-owned helper boundary instead of report_workflow.py private helpers.; Split canonical Week mapping from legacy compatibility reconstruction on the frontend so /week stays canonical-only.; Document the next bounded decomposition seam for report_workflow.py and main.py without performing the full decomposition in this feature.
- Out of scope: Deleting backend/app/services/report_workflow.py.; Fully decomposing backend/app/main.py.; Changing Week scoring, day semantics, explainability semantics, or payload contracts.; Rewriting backend/app/services/week_map.py in this wave.; Changing visible Week layouts or adding new Week UI states.
- Impacted modules: M-REPORT-WORKFLOW, M-WEEK-BRIEF-SEED, M-WEEK-BRIEF-SERVICE, M-FRONTEND-WEEK, M-WEEK-BRIEF-COMPATIBILITY
- Verification surfaces: WeekBrief service helper ownership and fallback behavior.; week_forecast report detail API payload stability.; Frontend canonical Week adapter fail-closed behavior.; Frontend compatibility reconstruction isolation.; Week fallback safety and canonical continuity at the route level.; Packet-local week_brief_* structured evidence review.
- Open decisions: Whether backend/app/services/week_map.py should be aligned to the new Week-owned seed helper in a later slice.; Whether the frontend compatibility helper remains test-only or later becomes an explicit secondary read-surface dependency.; How the next bounded extraction from backend/app/main.py should be staged after this boundary lands.

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
