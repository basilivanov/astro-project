# Review 0001 - FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING

status: accepted
reviewer: codex
source_hash: sha256:35ea0a87808e718004b6651368e21e4f25d985a40515b1d14462a7d7f6e1e749
reviewed_commit: 4edbfe8 + uncommitted implementation
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Accepted.

The implementation makes the intended local change: `_count_consecutive_failures()`
now skips `domain_status == "scope_blocked"` records after source-hash filtering
and before `_is_executor_failure()` sees a nonzero return code
(`prefect_grace/platform/executor_registry.py:301` through `:321`). This keeps
`scope_blocked` from incrementing or resetting executor-health streaks while
preserving true executor failure counting and deterministic executor selection.

No live agents, Prefect runs, worktrees, registry writes, backend/frontend,
Docker, Playwright, provider APIs, credentials, Git push, or merge were used
during review.

## Verification Reviewed

- Targeted pytest profile:
  `24 passed in 0.22s`.
- `python3 -m compileall -q prefect_grace/platform/executor_registry.py`: passed.
- Targeted GRACE lint:
  `executor_registry.py` passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`; artifact validation passed, with
  non-blocking `unknown_evidence_id` warnings from the current evidence
  contract parser.
- Scope check: `ok=true`, `outside_allowed=[]`, `frozen_violations=[]`.
- Independent reviewer proof:
  `scope_blocked + returncode=1` only history gives count `0`; mixed newest-first
  history `scope_blocked, agent_failed, success, older failure` gives count `1`.

## Observability Verdict

clean.

This is a local deterministic registry-policy fix. The evidence is bounded and
the packet preserves status-model and managed-runner behavior.
