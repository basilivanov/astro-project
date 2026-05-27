# Architect Handoff: FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ

- Slice ID: `SLICE-FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ`
- Slice dir: `/opt/astro-project/docs/backend-grace-observability-wave-tz`
- Goal: Reuse the existing backend active-slice canon and execute the remaining canon-sync plus dense dev-observability work in bounded waves without business-semantic drift.
- Scope: Close the remaining strict-GRACE contract and semantic gaps on the bounded backend active slice.; Add dense development-phase structured observability on the same bounded backend files.; Keep packet-local read-only evidence separate from the final canonical today-week closeout.; Use direct execution waves and keep planner off the critical path unless topology changes.
- Out of scope: DayBrief, WeekBrief, report-read, scheduler, analytics, billing, auth, referral, scoring, or frontend business changes.; Deep report_workflow decomposition.; Repo-wide logging redesign.; Frontend or visual work.
- Impacted modules: M-API-GATEWAY, M-TRACE-LOGGING, M-DAY-BRIEF-SERVICE, M-WEEK-BRIEF-SERVICE, M-ANALYTICS-EVENTS, M-OPS-AUTOMATION
- Verification surfaces: backend/app/main.py gateway startup, report-read, Today, DayBrief, and B2C report boundaries; backend/app/logging_utils.py payload shaping and JSONL routing; backend/app/middleware/correlation.py request-correlation state; backend/app/services/day_brief.py and day_brief_validators.py assembly, validation, fallback, and closeout markers; backend/app/services/week_brief_service.py payload, fallback, and envelope markers; backend/app/services/scheduler.py and backend/app/services/analytics.py job, persistence, branch, and failure markers plus read-only and today-week post-test review output
- Open decisions: No blocking architecture decision remains while the feature reuses the existing backend active-slice boundary already encoded in root GRACE.; Planner remains optional only; do not route through planner unless implementation or review forces a topology change.

Direct execution must treat the slice docs in this directory as the source of truth for wave scope, verification lanes, and observability ownership.
