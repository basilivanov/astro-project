# Backend GRACE Canon Sync + Full Dev Observability Verification Slice

Snapshot boundary: `git -C /opt/astro-project rev-parse HEAD`
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-SLICE-BACKEND-GRACE-OBS-WAVE-TZ-STRUCTURE` | `SCN-SLICE-BACKEND-CANON-ADDRESSABILITY` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py` | The targeted backend active-slice files expose stable strict-GRACE contracts, maps, required function contracts, and semantic blocks without business-semantic drift. |
| `VM-SLICE-BACKEND-GRACE-OBS-WAVE-TZ-PACKET-LOCAL` | `SCN-SLICE-BACKEND-DEV-OBS-DENSITY` | `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` | Packet-local evidence is readable by module, function, block, and correlation identifiers, and any non-emitted scheduler or analytics path is explicitly classified rather than silently omitted. |
| `VM-SLICE-BACKEND-GRACE-OBS-WAVE-TZ-WAVE-FINAL` | `SCN-SLICE-BACKEND-FINAL-CANONICAL-REVIEW` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py`; `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md` | Verifier and reviewer can reconstruct the canonical scenario history from module, function, block, event, correlation_id, and trace_id, and the final verdict is clean or degraded-but-expected with explicit rationale. |

## Evidence Rules

- Worker must attach exact commands executed and PASS or FAIL result.
- Worker must include file-level diff summary grouped by backend and tests.
- Post-test observability review is mandatory for W01, W02, and W03 because the slice touches Today and Week runtime emitters.
- `W01` and `W02` own packet-local evidence only; `W03` owns the canonical `today-week` closeout.

Architect slice directory: `/opt/astro-project/docs/backend-grace-observability-wave-tz`
