# Review 0002 - FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK

status: accepted
reviewer: codex
source_hash: sha256:29d95f8020fe2eb21758849334c115a777c4be00120d5d7553514f739d5e18ad
reviewed_commit: 2eb3a9d + uncommitted rework
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Accepted.

The review-0001 blockers are closed. The non-empty default recheck path now
uses the existing Prefect sync client factory before calling
`run_prefect_worker_binding_preflight()`, while retaining fail-closed behavior
when no client is available (`prefect_grace/platform/nightly_batch_recheck.py:492`
through `:526`). Saved plan integrity is now checked before confirmation:
declared totals, listed packet ids, current `max_packets`, and per-packet facts
all participate in blocker generation (`prefect_grace/platform/nightly_batch_recheck.py:284`
through `:307` and `:464` through `:490`).

No live agents, Prefect flow runs, registry writes, worktrees, Git mutations,
backend/frontend, Docker, Playwright, or provider calls were performed during
review.

## Rework Verification

- Packet-specified pytest profile:
  `65 passed in 14.48s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint passed for:
  `nightly_batch_recheck.py`, `nightly_batch_selection.py`,
  `prefect_smokes.py`, and `parser.py`.
- Strict packet validation: `ok=true`.
- Evidence manifest validation for `attempt-0002`: `ok=true`; artifact
  validation passed, with non-blocking `unknown_evidence_id` warnings from the
  current evidence contract parser.
- Scope check against `attempt-0002/changed_files.txt`: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`, `invalid_paths=[]`.
- Direct real-project CLI dry-run:
  `ok=true`, `preflight_status=ready`, `selected_total=0`, bounded JSON about
  1.9 KB, and all side-effect counters zero.
- Independent re-run of the review-0001 total/list mismatch repro now blocks:
  `PLAN_SELECTED_TOTAL_MISMATCH` and `CURRENT_MAX_PACKETS_EXCEEDED`.
- Independent re-run of the non-empty binding path now proves both branches:
  injected ready client gives `preflight_status=ready`; missing client blocks
  with `PREFECT_BINDING_NOT_READY`.

## Observability Verdict

clean.

The package now satisfies the stale-safe final recheck contract in dry-run and
injected modes. The only remaining operational limitation is expected: the real
project currently selects zero packets, so non-empty real Prefect readiness is
covered by injected client tests rather than by a live Prefect run.
