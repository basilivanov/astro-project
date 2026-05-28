# Review 0001 - FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN

status: rework_required
reviewer: codex
source_hash: sha256:d250cdebdfed15ccb1461ef68df055723a750043fa8b6a2b6a5e8c7db37a612b
reviewed_commit: 500885b + uncommitted implementation
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The new controlled runner has the right shape: dry-run default, explicit live
gates, bounded result fields, no merge flag on the new CLI, and injected tests
for the main happy/block paths. The remaining blockers are safety-contract
issues in exactly the paths that need to be fail-closed before real runs.

No live agents, Prefect flow runs, registry writes, worktrees, Git mutations,
backend/frontend, Docker, Playwright, or provider calls were performed during
review.

## Blockers

1. Unexpected degradation can stop the batch while still returning `ok=True`.

   `execute_batch_with_guard()` increments `passed_total` for a completed pilot
   before checking `_is_unexpected_degradation()` (`prefect_grace/platform/nightly_batch_execution_guard.py:499`
   through `:522`). The degradation branch sets `stop_reason` and increments
   `failed_total`, but it does not add a blocker and the final `ok` calculation
   only checks `executed_total > 0` and empty blockers (`:533`). A degraded run
   can therefore return success.

   Independent repro using the package's fake degradation pilot:

   ```text
   {'ok': True, 'stop_reason': 'unexpected_degradation', 'executed': 1, 'passed': 1, 'failed': 1, 'blockers': []}
   ```

   This violates the packet must-preserve rule to stop on first unexpected
   degradation and the acceptance criterion for injected live mode stop
   conditions. Required fix: unexpected degradation must be a failed/blocked
   terminal outcome with `ok=False`; add a structured blocker/error or make the
   final `ok` calculation include stop reasons/failure counters. Add a
   regression asserting `ok is False`, no additional packets execute, and the
   packet is not counted as passed.

2. `--execute --dry-run` enters live mode because the new CLI ignores the
   parsed `--dry-run` flag.

   The parser exposes both `--dry-run` and `--execute` on
   `run-nightly-controlled-batch` (`prefect_grace/cli_commands/parser.py:437`
   through `:452`), but the command handler computes
   `dry_run = not bool(args.execute)` (`prefect_grace/cli_commands/prefect_smokes.py:626`).
   As a result, an operator can pass both flags and the handler will still call
   the platform in live mode.

   Parser/handler repro:

   ```text
   {'execute': True, 'dry_run_arg': True}
   {'handler_dry_run': False}
   ```

   Dry-run must be an unambiguous safe mode. Required fix: make `--dry-run` and
   `--execute` mutually exclusive, or otherwise fail closed when both appear.
   Add a CLI regression for the conflict. Keep live execution requiring
   `--execute`, `--i-understand-live-batch`, and
   `GRACE_NIGHTLY_BATCH_EXECUTION_APPROVED=1`.

3. Lock-unavailable exits do not release or mark release, contrary to the
   packet lock contract.

   `run_nightly_controlled_batch()` returns immediately when lock acquisition
   fails (`prefect_grace/platform/nightly_controlled_batch_run.py:423` through
   `:431`), before entering the `try/finally` release path. The lower
   `execute_batch_with_guard()` has the same pattern
   (`prefect_grace/platform/nightly_batch_execution_guard.py:345` through
   `:351`). This leaves `lock_released=False` and never calls the injected
   lock's release method, even though the packet explicitly requires lock
   release after block/failure paths.

   Independent repro with an injected lock:

   ```text
   {'ok': False, 'stop_reason': 'lock_unavailable', 'lock_acquired': False, 'lock_released': False, 'release_calls': []}
   ```

   Required fix: call `lock.release(lock_result)` on lock-unavailable exits,
   update `lock_released`, and add injected regression tests for both the
   controlled runner and the execution guard if both remain in scope.

## Verification Reviewed

- Worker-reported targeted pytest profile: `61 passed`.
- Worker-reported compileall, targeted lint, strict packet validation,
  evidence manifest validation, and scope check passed.
- I independently reproduced the unexpected-degradation success state.
- I independently reproduced the `--execute --dry-run` ambiguity.
- I independently reproduced lock-unavailable release leakage.

## Observability Verdict

unexpected-degradation.

The implementation is bounded and avoids live side effects in reviewed paths,
but the safety gates are not yet strict enough for a controlled real packet
batch.
