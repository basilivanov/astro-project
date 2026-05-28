# Review 0002 - FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN

status: accepted
reviewer: codex
source_hash: sha256:d250cdebdfed15ccb1461ef68df055723a750043fa8b6a2b6a5e8c7db37a612b
reviewed_commit: 500885b + uncommitted rework
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Accepted.

The review-0001 safety blockers are closed. Unexpected degradation is now a
fail-closed terminal outcome with `ok=False`, `passed_total=0`, a structured
`UNEXPECTED_DEGRADATION` blocker, and no second packet execution
(`prefect_grace/platform/nightly_batch_execution_guard.py:508` through `:528`).
The ambiguous `--execute --dry-run` operator path is rejected by argparse through
a mutually exclusive group (`prefect_grace/cli_commands/parser.py:446` through
`:448`). Lock-unavailable exits now call the injected/no-op release path and
mark `lock_released=True` in both the controlled runner and the execution guard
(`prefect_grace/platform/nightly_controlled_batch_run.py:405` through `:411`;
`prefect_grace/platform/nightly_batch_execution_guard.py:347` through `:353`).

No live agents, Prefect flow runs, registry writes, worktrees, Git mutations,
backend/frontend, Docker, Playwright, or provider calls were performed during
review.

## Verification Reviewed

- Packet-specified pytest profile:
  `64 passed in 16.65s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint passed for:
  `nightly_controlled_batch_run.py`, `nightly_batch_execution_guard.py`,
  `prefect_smokes.py`, and `parser.py`.
- Strict packet validation: `ok=true`.
- Evidence manifest validation for `attempt-0002`: `ok=true`; artifact
  validation passed, with non-blocking `unknown_evidence_id` warnings from the
  current evidence contract parser.
- Scope check for reviewed files: `ok=true`, `outside_allowed=[]`,
  `frozen_violations=[]`, `invalid_paths=[]`.
- Direct dry-run CLI proof:
  `ok=true`, `stop_reason=no_packets_selected`, `executed_total=0`,
  zero agents/runs/Git mutations, lock released, bounded JSON.
- Direct missing-approval proof:
  exit `1`, `stop_reason=live_opt_in_blocked`, zero agents/runs, no recheck,
  lock released.
- Independent review-0001 repros now pass:
  unexpected degradation returns `ok=False`; `--execute --dry-run` exits `2`;
  lock-unavailable calls release and marks `lock_released=True`.

## Observability Verdict

clean.

The package is ready for the next controlled step. Real live controlled batch
execution was intentionally not run; live behavior is proven through injected
tests and approval-blocked CLI proof.
