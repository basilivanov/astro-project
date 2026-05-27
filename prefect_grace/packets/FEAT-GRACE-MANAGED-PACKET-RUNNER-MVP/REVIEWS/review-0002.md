# Review 0002 — FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework required.

The two blockers from review-0001 are mostly addressed:

- plain `--execute-agent` now fails before the launcher path;
- same `packet_id` / `attempt` dry-run can reuse the existing worktree.

However, the CLI still does not make dry-run the true default, which was an explicit acceptance requirement and part of the previous required rework.

## Checks

Targeted tests:

```text
51 passed in 6.49s
```

Regression tests:

```text
65 passed in 3.14s
```

Static checks:

```text
compileall PASS
managed_packet_runner GRACE lint PASS
managed_packet_runner_flow GRACE lint PASS
managed_packet_artifacts GRACE lint PASS
codex_launcher GRACE lint PASS
packet_ok True
source_hash sha256:d2b8920f61c7f4e2ea6715cb735209b001777209416e47e0d3a9d4998cbb6d03
```

Manual blocker repro checks:

```text
run-managed-packet --execute-agent --json
exit 2
error code MISSING_EXPLICIT_NO_DRY_RUN
```

```text
run-managed-packet --dry-run --json
run-managed-packet --dry-run --json
first exit 0
second exit 0
```

## Resolved

### Review-0001 blocker 1 is partially resolved

Plain `--execute-agent` now fails closed before reaching the launcher path.

Current error:

```json
{
  "code": "MISSING_EXPLICIT_NO_DRY_RUN",
  "message": "Live agent execution requires explicit --no-dry-run flag. Use: --execute-agent --no-dry-run"
}
```

### Review-0001 blocker 2 is resolved

`run_managed_packet(...)` now calls `manager.status(packet_id=..., attempt=...)` before creating a worktree, and reuses an existing worktree when present.

Relevant code:

- `prefect_grace/platform/managed_packet_runner.py:174`
- `prefect_grace/platform/managed_packet_runner.py:177`
- `prefect_grace/platform/managed_packet_runner.py:183`

## Remaining Blocker

### CLI dry-run is still not the true default

The packet requires:

```text
--dry-run default behavior; must not launch a live agent.
```

Review-0001 also required:

```text
Make CLI dry-run the true default.
```

Current parser behavior:

```python
args = build_parser().parse_args([
    "run-managed-packet",
    "--packet", "p",
    "--repo-root", "r",
    "--worktree-root", "w",
    "--project-key", "k",
    "--packet-id", "id",
    "--attempt", "1",
    "--base-ref", "HEAD",
])
```

Observed:

```text
dry_run False
execute_agent False
```

Cause:

- `prefect_grace/cli.py:1713` uses `--dry-run` with `action="store_true"` and no `default=True`.
- `prefect_grace/cli.py:1714` sets `--no-dry-run`, but only when explicitly passed.

This means the no-flag operator path is not actually `dry_run=True`; it is `dry_run=False, execute_agent=False`. It does not launch a live agent, but it is not the contract's dry-run default and it weakens later submission semantics where dry-run status must be machine-readable.

Required fix:

1. Set `run-managed-packet` parser default to `dry_run=True`.
2. Keep `--execute-agent` rejected unless `--no-dry-run` is explicitly provided.
3. Add a parser or CLI regression test proving no flags gives `dry_run=True`.
4. Add a CLI smoke test proving no flags returns `agent_result.dry_run == true`.
5. Re-run the same verification set.

## Acceptance Criteria For Next Review

- `run-managed-packet` with no `--dry-run` / `--no-dry-run` parses to `dry_run=True`.
- `run-managed-packet --execute-agent` exits 2 before invoking flow/launcher.
- `run-managed-packet --execute-agent --no-dry-run` remains the only live-agent-intent combination.
- repeated same `packet_id` / `attempt` dry-run remains green.
- targeted/regression/static checks remain green.

## Notes

Do not broaden the rework. The implementation is otherwise close to acceptance.
