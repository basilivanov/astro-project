# Backend Active Slice GRACE Canon Sync Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-BACKEND-ACTIVE-CANON-PACKET-LOCAL` | `SCN-SLICE-BACKEND-PACKET-LOCAL-EVIDENCE` | docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py; python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | W01 implementation evidence remains packet-local and does not claim canonical today-week closeout; verifier or reviewer can attribute relevant evidence or explicit evidence gaps without silent scope expansion. |
| `VM-BACKEND-ACTIVE-CANON-SYNC` | `SCN-SLICE-BACKEND-EVIDENCE-READABILITY` | docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py; python3 tools/post_test_review.py --profile today-week --since 30m --report-format md | W02 final post-test evidence for Day, Week, and nearby report-read activity is readable by module/function/block names without guesswork, and any scheduler or analytics evidence gap is explicitly recorded. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/backend-active-slice-grace-canon-sync`
