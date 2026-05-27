# Review 0001 — FEAT-GRACE-EXECUTOR-REGISTRY-MVP

status: rework_required
reviewer: codex
source_hash: sha256:2553a049aab620ebd94ac94d73c89166b3319c783c81d989ff381cd71d2e1743
attempt: attempt-0001
reviewed_at: 2026-05-26

## Verdict

The implementation is directionally correct, but the packet cannot be accepted
yet because the exact verification contract does not reproduce and the evidence
scope is not clean.

## Blocking Issues

### 1. Packet-targeted verification references a missing test file

The packet's required targeted test command includes:

```bash
tests/test_prefect_grace_managed_packet_runner_executor_registry.py
```

That file does not exist in the workspace, so the exact packet verification
fails before running tests:

```text
no tests ran in 0.00s
ERROR: file or directory not found: tests/test_prefect_grace_managed_packet_runner_executor_registry.py
```

This must be fixed by either:

- adding the missing test file with managed-runner executor-registry coverage; or
- updating the packet contract and evidence to use the actual test file that
  covers this integration.

Acceptance requires the exact `## Verification` command from
`EXECUTION_PACKET.md` to pass.

### 2. Evidence scope is not limited to Allowed Write Scope

`EVIDENCE/attempt-0001/git_diff_name_only.txt` includes paths outside the
packet's allowed scope, including:

```text
automation/cli_health.yaml
prefect_grace/briefs/backend_grace_contracts_observability_hubs_20260417.yaml
prefect_grace/briefs/backend_grace_observability_wave_tz.yaml
prefect_grace/briefs/backend_grace_wave_finish_20260417.yaml
prefect_grace/prompts/canon_digest_prompt.md
```

The packet expected evidence explicitly requires:

```text
git diff --name-only limited to Allowed Write Scope
```

Attempt evidence therefore cannot be used as acceptance evidence. Rework must
produce a clean diff report limited to:

- executor registry implementation files;
- project adapter / managed runner / CLI files allowed by this packet;
- executor-registry tests;
- packet-local evidence/review artifacts.

## Confirmed Passing Checks

The following checks passed during review and do not need redesign:

```bash
pytest -q \
  tests/test_prefect_grace_executor_registry.py \
  tests/test_prefect_grace_executor_registry_cli.py \
  tests/test_prefect_grace_project_adapter_executors.py \
  tests/test_prefect_grace_cli_contracts.py
```

Result:

```text
37 passed in 3.55s
```

The existing managed-runner regression plus executor tests also passed:

```bash
pytest -q \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_executor_registry.py \
  tests/test_prefect_grace_executor_registry_cli.py \
  tests/test_prefect_grace_project_adapter_executors.py \
  tests/test_prefect_grace_cli_contracts.py
```

Result:

```text
45 passed in 3.96s
```

Static checks passed:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/executor_registry.py
python3 scripts/grace_lint.py prefect_grace/platform/project_adapter.py
python3 scripts/grace_lint.py prefect_grace/platform/managed_packet_runner.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md \
  --strict --json
```

CLI smoke passed without launching live agents:

```bash
python3 -m prefect_grace.cli list-executors --project /opt/astro-project --json
python3 -m prefect_grace.cli select-executor --project /opt/astro-project --packet-id SOME-PACKET --json
```

## Required Rework

1. Add or correct the managed-runner executor-registry integration test named
   in the packet verification command.
2. Re-run the exact targeted verification command from the packet.
3. Rebuild `attempt-0002` evidence with `git_diff_name_only.txt` showing only
   allowed-scope paths.
4. Keep frozen scope unchanged, especially:
   - `scripts/grace_lint.py`;
   - `prefect_grace/tasks/codex_launcher.py`;
   - `prefect_grace/platform/state_store.py`;
   - Prefect flow/deployment files.

## Reviewer Notes

No product backend/frontend verification is required for this packet. This is
an offline orchestration-layer change and no live agents should be started.
