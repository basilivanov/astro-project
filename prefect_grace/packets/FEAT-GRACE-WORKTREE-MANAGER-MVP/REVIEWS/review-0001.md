# Review 0001 — FEAT-GRACE-WORKTREE-MANAGER-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework required.

The submitted changes do not implement `FEAT-GRACE-WORKTREE-MANAGER-MVP`. They implement `FEAT-GRACE-SCOPE-GUARD-MVP`.

## Blockers

### 1. Worktree Manager module is missing

Expected by packet:

```text
prefect_grace/platform/worktree_manager.py
```

Actual:

```text
worktree_manager_exists = no
```

There is no `WorktreeManager`, no `WorktreeContext`, no `WorktreeStatus`, no branch sanitizer, no git runner, and no changed-file extraction.

### 2. Worktree Manager tests are missing

Expected by packet:

```text
tests/test_prefect_grace_worktree_manager.py
tests/test_prefect_grace_cli_worktree_manager.py
```

Actual verification:

```text
pytest -q tests/test_prefect_grace_worktree_manager.py tests/test_prefect_grace_cli_worktree_manager.py tests/test_prefect_grace_cli_contracts.py
ERROR: file or directory not found: tests/test_prefect_grace_worktree_manager.py
exit code = 4
```

### 3. Required CLI surface is missing

Expected commands:

```text
worktree-create
worktree-status
worktree-cleanup
```

Actual submitted CLI work adds `check-scope`, which belongs to Scope Guard, not Worktree Manager.

### 4. Evidence is for Scope Guard, not Worktree Manager

Worktree packet evidence directory contains only the packet source:

```text
prefect_grace/packets/FEAT-GRACE-WORKTREE-MANAGER-MVP/EXECUTION_PACKET.md
```

Scope Guard evidence exists under:

```text
prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP/EVIDENCE/attempt-0001/
```

## Required Rework

Implement the actual Worktree Manager packet:

1. Add `prefect_grace/platform/worktree_manager.py`.
2. Add `WorktreeContext`, `WorktreeStatus`, and `WorktreeManager`.
3. Add deterministic branch sanitizer.
4. Add safe git runner with explicit `cwd` and no shell interpolation.
5. Add changed-file extraction for committed, staged, unstaged, and untracked paths.
6. Add cleanup safety: never remove outside configured `worktree_root`.
7. Add CLI commands `worktree-create`, `worktree-status`, `worktree-cleanup`.
8. Add tests using temporary git repositories only.
9. Run the Worktree packet verification commands.

## Acceptance Criteria For Next Review

- `prefect_grace/platform/worktree_manager.py` exists and passes GRACE lint.
- Worktree targeted tests exist and pass.
- CLI worktree commands exist and pass smoke tests in a temporary git repository.
- Main `/opt/astro-project` workspace is not mutated by tests.
- No remote push, merge, live agent, Prefect deployment, Docker container, or product service is started.
