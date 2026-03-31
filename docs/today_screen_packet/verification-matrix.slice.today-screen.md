# Today Screen Review Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-TODAY-SCREEN-REVIEW`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-TODAY-HERO-CLEAN` | `SCN-TODAY-HERO-CLEAN`, `SCN-TODAY-MOON-DEDUPE` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; targeted frontend assertions around Today hero rendering | Hero shows one verdict path only; moon context remains compact and non-duplicative. |
| `VM-TODAY-RAW-TAGS` | `SCN-TODAY-NO-RAW-TAGS`, `SCN-TODAY-NO-FALSE-BIRTHTIME` | `./scripts/run_e2e.sh --last-failed`; targeted `quality` or `today` spec | No raw service tags or misleading birth-time warning visible on Today UI. |
| `VM-TODAY-DETAIL-LAYER` | `SCN-TODAY-SCORES-DETAIL`, `SCN-TODAY-WINDOWS-DETAIL`, `SCN-TODAY-RISKS-DETAIL` | targeted backend tests for DTO shape; targeted e2e/spec for detail expansion | Expandable details render only when present and never leak raw fields. |

## Evidence rules

- Worker MUST attach the exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- If a spec is missing for a reproduced defect, worker MUST add or update a deterministic reproduction test before claiming green.
- If `--last-failed` is empty/non-informative, worker MUST run a targeted Today/quality spec instead of stopping at a no-op.
