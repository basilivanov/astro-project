# Review 0003 — FEAT-GRACE-STATUS-MODEL-MVP

status: rework_required
reviewer: codex
source_hash: sha256:5fc722553837d1a2b340a35a757f61460f0a1f6712196ab88c7ce71cf8d876a2
attempt: attempt-0002
reviewed_at: 2026-05-27

## Verdict

Rework required.

## What Passed

- Status model module remains structurally sound.
- Targeted verification passed: `116 passed, 1 skipped`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- GRACE lint for `prefect_grace/platform/status_model.py`: passed.
- Packet validation: passed.
- Frozen scope remains clean for `feature_pipeline.py`, `codex_launcher.py`, product code, scripts, and state files.

## Blocking Issues

### 1. Allowed write scope violation: `e2e_packet_runner.py`

The packet allowed implementation changes only in:

- `prefect_grace/platform/status_model.py`;
- `prefect_grace/platform/backlog_controller.py`;
- `prefect_grace/platform/managed_packet_runner.py`;
- `prefect_grace/platform/worktree_scope_lifecycle.py`;
- `prefect_grace/platform/verifier_reviewer_handoff.py`;
- `prefect_grace/platform/executor_registry.py`;
- `prefect_grace/cli.py`.

Current diff includes:

- `prefect_grace/platform/e2e_packet_runner.py`.

That file is outside this packet's allowed write scope. Either revert the E2E runner status-model changes for this packet, or amend the packet source contract first and re-run as a fresh source-hash attempt.

### 2. Required focused integration is still incomplete

The packet explicitly requires focused integration in:

- `backlog_controller.py`;
- `managed_packet_runner.py`;
- `worktree_scope_lifecycle.py`;
- `verifier_reviewer_handoff.py`;
- `executor_registry.py`.

Current usages of `status_model` exist only in:

- `managed_packet_runner.py`;
- `verifier_reviewer_handoff.py`;
- out-of-scope `e2e_packet_runner.py`.

There are still no usages in:

- `backlog_controller.py`;
- `worktree_scope_lifecycle.py`;
- `executor_registry.py`.

This means registry and executor failure/status paths still rely on raw string drift in the modules this packet was created to stabilize.

## Required Fix

Keep the rework small:

1. Remove or defer `e2e_packet_runner.py` changes unless the packet contract is amended before implementation.
2. Add narrow status-model usage to the missing required modules:
   - `backlog_controller.py`: use `RegistryStatus` / normalization for focused registry status comparisons or writes.
   - `worktree_scope_lifecycle.py`: use `DomainStatus.CHECK_PASSED.value` and `DomainStatus.SCOPE_BLOCKED.value` for emitted domain statuses.
   - `executor_registry.py`: use normalized `DomainStatus` when deciding whether an execution result is an executor failure.
3. Preserve all public JSON status strings as strings.
4. Do not edit `feature_pipeline.py` or `codex_launcher.py`.

## Notes

- The tests are green, but they do not satisfy the packet objective yet because the runtime modules named in the packet are not all integrated.
- This should be a bounded rework, not a broad migration.
