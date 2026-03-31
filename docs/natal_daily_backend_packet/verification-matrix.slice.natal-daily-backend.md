# Verification Matrix — Natal + Daily Backend Slice

| VM ID | Slice Surface | Commands | Pass Signal | Known Allowed Gap |
| --- | --- | --- | --- | --- |
| `VM-NATAL-CONTEXT` | Natal context/report truth path in `backend/app/services/report_workflow.py` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `docker exec astro-project-backend-1 python3 -m pytest -q tests/verify_natal_generation.py tests/test_report_contract.py` | `section_context` / report context stay deterministic, `birth_time_known` gating holds, natal generation contract stays intact. | Does not prove full live editorial quality across all models. |
| `VM-NATAL-SUMMARY-REPAIR` | `executive_summary` / `final_synthesis` fallback and repair boundaries | `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_validation_relaxed.py tests/test_validation_template_fallback.py tests/verify_natal_generation.py` | Summary-layer output stays chart-specific, fallback is compact and user-safe, repair leakage is absent in deterministic paths. | Live reruns may still expose editorial variance; this VM proves bounded acceptance/fallback only. |
| `VM-DAY-BRIEF-CONTRACT` | Day-brief schema, validator, and repair path | `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py` | Day-brief output stays schema-valid, readable, and backward compatible under repair/fallback. | Does not prove frontend rendering or unrelated weekly/monthly products. |
| `VM-DAILY-FEED-ROBUSTNESS` | Personalized daily facts layer and `/api/feed/today` fallback contract | `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py tests/verify_daily_feed.py`; `python3 scripts/verify_api_responses.py` | Feed remains safe, deterministic, auth-safe, and backward compatible; `traffic_lights` contract holds. | Homepage E2E drift in some mock-only frontend assertions remains a separate frontend follow-up. |
| `VM-SLICE-BACKEND-QUICK` | Mandatory backend quick profile for every substantial backend change | `docker exec astro-project-backend-1 python3 scripts/pipeline.py` | Core backend quick profile is green before handoff. | Not a substitute for the targeted VM bundles above. |

## Slice Rules

- PASS means the exact command bundle is green and no contract-breaking fallback is hidden behind a nominal success.
- Fallback is acceptable only when the slice explicitly allows degraded success with readable, schema-safe, backward-compatible output.
- If a repro bug exists in natal/day-brief/daily-feed paths, the worker must add or update targeted regression coverage before the fix.
- This matrix is backend-only; frontend, billing, bot, admin, and broad product rollout remain frozen for this slice.
