# Review 0004 — FEAT-GRACE-STATUS-MODEL-MVP

status: rework_required
reviewer: codex
source_hash: sha256:5fc722553837d1a2b340a35a757f61460f0a1f6712196ab88c7ce71cf8d876a2
attempt: attempt-0003
reviewed_at: 2026-05-27

## Verdict

Rework required.

## What Passed

- Targeted verification passed: `104 passed in 2.85s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- GRACE lint for `prefect_grace/platform/status_model.py`: passed.
- Packet validation: passed.
- Frozen scope is clean.
- Previous out-of-scope `e2e_packet_runner.py` change was reverted.
- Status model is now used in:
  - `backlog_controller.py`;
  - `managed_packet_runner.py`;
  - `verifier_reviewer_handoff.py`;
  - `executor_registry.py`.

## Blocking Issue

### 1. `worktree_scope_lifecycle.py` integration is still missing

The packet explicitly requires focused integration in `worktree_scope_lifecycle.py`:

> `worktree_scope_lifecycle.py`: `passed` / `scope_blocked` normalization.

Current diff does not include `prefect_grace/platform/worktree_scope_lifecycle.py`, and direct search shows raw literals remain there:

- `Literal["passed", "scope_blocked", "worktree_error"]`;
- `status="passed"`;
- `status="scope_blocked"`.

That keeps one runtime boundary outside the centralized status model.

## Required Fix

Keep the fix minimal:

1. Import `DomainStatus` in `worktree_scope_lifecycle.py`.
2. Replace emitted status values with:
   - `DomainStatus.CHECK_PASSED.value` for `passed`;
   - `DomainStatus.SCOPE_BLOCKED.value` for `scope_blocked`.
3. Leave `worktree_error` as-is only if it is intentionally a lifecycle-local status rather than a domain status; otherwise map it through `DomainStatus.RUNNER_ERROR.value` with tests.
4. Add/adjust a small test proving public output remains string values.

## Notes

- Do not edit `feature_pipeline.py` or `codex_launcher.py`.
- Do not reintroduce `e2e_packet_runner.py` changes in this packet.
- This is now a very small final rework.
