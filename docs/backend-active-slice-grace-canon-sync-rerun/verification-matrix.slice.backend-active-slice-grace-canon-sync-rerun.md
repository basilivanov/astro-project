# Backend Active Slice GRACE Canon Sync Rerun Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-BACKEND-ACTIVE-CANON-STRUCTURE-RERUN-2` | `SCN-SLICE-BACKEND-MODULE-ADDRESSABILITY-RERUN-2`, `SCN-SLICE-BACKEND-ENTRYPOINT-CONTRACTS-RERUN-2` | `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py` | Touched backend active-slice files expose strict-GRACE module contracts, module maps, required function contracts, and stable semantic START/END blocks without changing the covered business behavior. |
| `VM-BACKEND-ACTIVE-CANON-PIPELINE-RERUN-2` | `SCN-SLICE-BACKEND-ENTRYPOINT-CONTRACTS-RERUN-2` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py` | Backend quick profile remains green after the bounded canon-sync rerun changes. |
| `VM-BACKEND-ACTIVE-CANON-PACKET-LOCAL-RERUN-2` | `SCN-SLICE-BACKEND-PACKET-LOCAL-EVIDENCE-RERUN-2` | `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md` | W01 implementation evidence remains packet-local and does not claim canonical today-week closeout; reviewer can still attribute evidence or explicit evidence gaps by module/function/block names. |
| `VM-BACKEND-ACTIVE-CANON-WAVE-FINAL-RERUN-2` | `SCN-SLICE-BACKEND-WAVE-FINAL-EVIDENCE-RERUN-2` | `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md` | W02 final evidence owns canonical today-week observability and publishes an explicit clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker verdict for the touched backend active slice. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- W01 implementation gates use packet-local evidence only and may run `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`; they must not treat that as canonical today-week closeout.
- W02 final verifier owns canonical `today-week` observability and must classify the verdict as `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.
- Post-test observability review is mandatory because the slice touches Today/Week backend emitters, but evidence ownership must match the active packet lane.

Architect slice directory: `/opt/astro-project/docs/backend-active-slice-grace-canon-sync-rerun`
