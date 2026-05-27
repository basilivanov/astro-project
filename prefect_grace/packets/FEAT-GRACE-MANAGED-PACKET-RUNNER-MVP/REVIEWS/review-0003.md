# Review 0003 — FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP

status: accepted
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Accepted.

All blockers from review-0001 and review-0002 are resolved.

## Checks

Parser safety check:

```text
<no-flags>                 dry_run=True  execute_agent=False explicit_no_dry=False
--execute-agent            dry_run=True  execute_agent=True  explicit_no_dry=False
--execute-agent --no-dry-run dry_run=False execute_agent=True explicit_no_dry=True
--dry-run                  dry_run=True  execute_agent=False explicit_no_dry=False
```

Manual CLI behavior:

```text
run-managed-packet --json
exit 0
domain_status passed
agent_result.dry_run true
```

```text
run-managed-packet --execute-agent --json
exit 2
error code MISSING_EXPLICIT_NO_DRY_RUN
```

```text
run-managed-packet --dry-run --json
run-managed-packet --dry-run --json
first exit 0, domain_status passed
second exit 0, domain_status passed
same worktree path reused
```

Targeted tests:

```text
52 passed in 6.77s
```

Regression tests:

```text
65 passed in 3.51s
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

## Accepted Scope

Accepted implementation scope:

- `prefect_grace/platform/managed_packet_runner.py`
- `prefect_grace/flows/managed_packet_runner_flow.py`
- `prefect_grace/tasks/managed_packet_artifacts.py`
- `prefect_grace/tasks/codex_launcher.py`
- `prefect_grace/cli.py`
- packet-declared tests

`scripts/grace_lint.py` has no diff.

## Notes

The managed runner now satisfies the required safety properties:

- dry-run is the true CLI default;
- live agent execution requires explicit `--execute-agent --no-dry-run`;
- the agent receives the isolated worktree path through `workdir_override`;
- repeated same `packet_id` / `attempt` resolves the existing worktree;
- `scope_blocked` has priority over `agent_failed`;
- artifact publication is best-effort and does not hide domain status.

Operational note for later submission work: use a stable project worktree root for a packet attempt. Reusing the same branch name across different worktree roots in one git repo can still conflict at git-worktree level; this is expected and should be avoided by the native submission layer.
