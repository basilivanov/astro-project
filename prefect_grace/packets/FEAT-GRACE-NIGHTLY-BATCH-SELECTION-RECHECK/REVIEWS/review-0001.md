# Review 0001 - FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK

status: rework_required
reviewer: codex
source_hash: sha256:29d95f8020fe2eb21758849334c115a777c4be00120d5d7553514f739d5e18ad
reviewed_commit: 2eb3a9d + uncommitted implementation
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The stale source, registry status, dependency, review, evidence, lock, scope,
and bounded-output tests are in place, and the implementation stayed in the
packet write scope. The remaining blockers are both in the execution contract:
the CLI path cannot confirm a non-empty clean plan with real Prefect binding,
and saved plan totals can be silently weakened when the persisted selected
packet list is incomplete or truncated.

No live agents, Prefect flow runs, registry writes, worktrees, Git mutations,
backend/frontend, Docker, Playwright, or provider calls were performed during
review.

## Blockers

1. Non-empty CLI recheck cannot confirm real Prefect binding.

   `nightly-recheck-batch` calls `recheck_nightly_batch()` without providing a
   binding checker or Prefect client (`prefect_grace/cli_commands/prefect_smokes.py:508`
   through `:515`). For any non-empty saved plan, `recheck_nightly_batch()`
   falls back to `run_prefect_worker_binding_preflight()` with no
   `prefect_client` (`prefect_grace/platform/nightly_batch_recheck.py:447`
   through `:459`). That platform preflight is intentionally fail-closed when
   no client is injected, so a clean selected batch is always blocked with
   `PREFECT_CLIENT_REQUIRED` instead of checking the actual worker binding.

   Independent temp-project repro:

   ```text
   {'ok': False, 'preflight_status': 'blocked', 'blockers': ['PREFECT_BINDING_NOT_READY'], 'errors': [{'type': 'PREFECT_CLIENT_REQUIRED', 'message': 'Prefect client must be injected (no client provided)'}]}
   ```

   This violates the objective to re-read Prefect binding status immediately
   before controlled batch execution. It also means the command can only pass
   the current real-project proof because `selected_total=0`; the first
   non-empty real nightly selection would fail for wiring reasons, not because
   deployment/pool/queue state was actually bad.

   Required fix: wire the CLI/default recheck path through the existing
   `create_prefect_sync_client()` path used by `prefect-worker-binding`, or
   introduce an explicit adapter so non-empty recheck validates live binding
   when Prefect is available and fails closed only when it is not. Add CLI or
   platform coverage proving a clean non-empty saved plan can become ready with
   a real/injected binding client and that missing client remains blocked.

2. Saved plan totals are not trusted or validated, so incomplete/truncated
   plans can pass as ready.

   `BatchSelectionResult.to_dict()` bounds `selected_packets` and
   `selected_packet_facts` to `MAX_ITEMS` while preserving `selected_total`
   (`prefect_grace/platform/nightly_batch_selection.py:158` through `:166`).
   The recheck then discards the saved `selected_total` and replaces it with
   `len(selected_packets)` (`prefect_grace/platform/nightly_batch_recheck.py:427`
   through `:440`). If a saved plan declares more packets than are present in
   the bounded or malformed list, recheck only checks the listed subset and can
   miss the current `max_packets` limit or stale state for omitted packets.

   Independent temp-project repro with a saved plan declaring
   `selected_total=2`, one listed packet, and current `max_packets=1`:

   ```text
   {'ok': True, 'preflight_status': 'ready', 'selected_total': 1, 'blockers': []}
   ```

   The acceptance criteria require selected batches exceeding current limits
   and stale selected packets to block. This path makes the gate stale-unsafe
   for any incomplete saved plan and especially for operator JSON saved from a
   selection larger than `MAX_ITEMS`.

   Required fix: fail closed when the saved declared total does not match the
   number of selected packet ids available for recheck, or provide a separate
   complete machine-readable selection artifact for recheck while keeping
   operator output bounded. Also require one fact per selected packet before a
   packet can be confirmed. Add regression coverage for total/list mismatch,
   selected packet without matching fact, and a batch above current
   `max_packets`.

## Verification Reviewed

- Packet-specified pytest profile:
  `59 passed in 14.39s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint:
  `nightly_batch_recheck.py`, `nightly_batch_selection.py`,
  `prefect_smokes.py`, and `parser.py` passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`; artifact validation passed, with
  non-blocking `unknown_evidence_id` warnings from the current evidence
  contract parser.
- Scope check against the packet allowed scope: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`, `invalid_paths=[]`.
- Direct real-project dry-run recheck: `ok=true`, but only for
  `selected_total=0`, so it does not exercise Prefect binding readiness.
- Independent temp repros proved the no-client binding failure and the saved
  total/list mismatch bypass.

## Observability Verdict

unexpected-degradation.

The implementation is read-only and bounded, but the final gate is not yet
usable for a non-empty real batch and can accept an incomplete saved plan.
