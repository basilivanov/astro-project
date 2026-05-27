# Review 0001 — FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework required.

The implementation is close and the declared test suite passes, but two acceptance-critical semantics from the packet are not implemented safely enough.

## What Passed

Targeted tests:

```text
49 passed in 4.11s
```

Regression tests:

```text
65 passed in 3.27s
```

Static checks:

```text
compileall PASS
managed_packet_runner GRACE lint PASS
managed_packet_runner_flow GRACE lint PASS
managed_packet_artifacts GRACE lint PASS
codex_launcher GRACE lint PASS
packet validation PASS
source_hash sha256:d2b8920f61c7f4e2ea6715cb735209b001777209416e47e0d3a9d4998cbb6d03
```

Scope is mostly correct: implementation is limited to the packet's declared modules/tests. `scripts/grace_lint.py` has no diff.

## Blockers

### 1. `run-managed-packet --execute-agent` can enter live execution without explicit `--no-dry-run`

The packet requires:

> `--execute-agent` without explicitly disabling dry-run must fail closed with a clear input error.

Current parser:

- `prefect_grace/cli.py:1713`
- `prefect_grace/cli.py:1714`
- `prefect_grace/cli.py:1715`

`--dry-run` uses `action="store_true"` without `default=True`, so omitting `--dry-run` makes `args.dry_run == False`.

Current safety check:

- `prefect_grace/cli.py:1309`
- `prefect_grace/cli.py:1310`

This only rejects `--execute-agent --dry-run`. It does not reject plain `--execute-agent`, so the command reaches the live-agent path.

Reproduction command:

```bash
python3 -m prefect_grace.cli run-managed-packet \
  --packet /tmp/.../EXECUTION_PACKET.md \
  --repo-root /tmp/.../repo \
  --worktree-root /tmp/.../repo.worktrees \
  --project-key test-project \
  --packet-id TEST-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --execute-agent \
  --json
```

Observed result:

```json
{
  "domain_status": "runner_error",
  "blocker_reason": "Agent launch failed: 'No packets.packets record with packet_id=TEST-W01-PACKET'"
}
```

The command did not launch Codex only because the test packet was absent from the legacy packet state store. With a real packet record it would proceed into the launcher path.

Required fix:

1. Make CLI dry-run the true default.
2. Require an explicit `--no-dry-run` together with `--execute-agent` for live execution.
3. Add a regression test for plain `--execute-agent` proving it fails before any launcher/flow path.
4. Keep `--execute-agent --dry-run` rejected.
5. Keep `--execute-agent --no-dry-run` allowed.

Implementation options:

- use `parser.set_defaults(dry_run=True)` plus an explicit flag-state sentinel; or
- use mutually clear flags such as `--dry-run` default true and `--live-agent` requiring `--no-dry-run`; or
- track whether `--no-dry-run` was explicitly provided.

The important requirement is explicit operator intent, not just the final boolean value.

### 2. Managed runner always creates a new worktree and fails on existing packet attempt

The packet requires the managed runner to create or resolve the packet worktree.

Current code:

- `prefect_grace/platform/managed_packet_runner.py:166`
- `prefect_grace/platform/managed_packet_runner.py:173`

It calls `manager.create_packet_worktree(...)` unconditionally.

Reproduction:

```bash
python3 -m prefect_grace.cli run-managed-packet ... --attempt 1 --dry-run --json
python3 -m prefect_grace.cli run-managed-packet ... --attempt 1 --dry-run --json
```

First run:

```text
exit 0
```

Second run:

```json
{
  "domain_status": "runner_error",
  "blocker_reason": "Worktree creation failed: Command '['git', 'worktree', 'add', '-B', ...] returned non-zero exit status 128."
}
```

This breaks retry/re-entry semantics for the same packet attempt. Prefect retry or operator rerun should be able to resolve the existing worktree and continue evaluating it, not fail during setup.

Required fix:

1. Before creating, call `manager.status(packet_id=..., attempt=...)`.
2. If the worktree exists, use the existing worktree context/path/branch.
3. If absent, create it.
4. Add a regression test that running the same packet/attempt twice returns a clean domain result instead of `runner_error`.

## Required Rework

1. Fix CLI dry-run/live-agent gating.
2. Fix managed runner create-or-resolve worktree behavior.
3. Add tests covering both blockers.
4. Re-run the targeted tests, regression tests, compile, GRACE lint, strict packet validation, and CLI smoke.
5. Confirm diff scope remains inside `Allowed Write Scope`.

## Notes

The core domain status priority is otherwise correct: `scope_blocked` wins over `agent_failed`.

The `workdir_override` implementation in `codex_launcher.py` is narrow and matches the packet intent. Keep it unchanged except for tests if needed.
