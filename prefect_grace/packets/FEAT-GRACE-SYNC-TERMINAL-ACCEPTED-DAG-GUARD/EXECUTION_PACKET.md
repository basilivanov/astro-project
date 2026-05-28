# Execution Packet: FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD-W01-ACCEPTED-DAG-FILTER

## Objective

Prevent `sync-packets` and `submit-packets --dry-run` from reporting unchanged
terminal accepted runtime registry records as blocked only because old source
packets still contain legacy dependency ids.

The guard must apply only when the runtime registry status is `accepted` and
the source hash is unchanged. Changed accepted source packets, ready packets,
and other nonterminal records must continue to fail closed on missing
dependencies.

## Slice

- slice_id: `SLICE-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD`
- slice_slug: `grace-sync-terminal-accepted-dag-guard`
- feature_id: `FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD`
- packet_id: `FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD-W01-ACCEPTED-DAG-FILTER`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME, FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP-W01-BACKLOG-BOOTSTRAP`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD`

## Source Of Truth

- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/dag.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`

## Impacted Modules

- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-STRICT-PACKET-DISCOVERY`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/prompts/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/SUMMARY.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Source packet dependency ids in old accepted packets are not rewritten.
- `sync-packets --dry-run` does not mutate runtime registry state.
- `submit-packets --dry-run` creates no Prefect runs.
- Accepted registry records with changed source hashes are not hidden by the guard.
- Ready and nonterminal records with missing dependencies still warn and block.
- Existing CLI JSON envelopes keep `result` equal to `data`.
- No live agents, Prefect runs, Docker, backend, frontend, Playwright, provider APIs, or credentials are used.

## Verification

- `pytest -q tests/test_prefect_grace_backlog_controller.py tests/test_prefect_grace_prefect_native_submission.py tests/test_prefect_grace_cli_contracts.py`
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli_commands prefect_grace/cli.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/backlog_controller.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-SYNC-TERMINAL-ACCEPTED-DAG-GUARD/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli sync-packets --dry-run --json`
- `python3 -m prefect_grace.cli submit-packets --project prefect_grace/project.yaml --dry-run --json`
- `git diff --check`

## Expected Evidence

- `targeted_pytest.txt`
- `compile_output.txt`
- `lint_output.txt`
- `sync_real_project_dry_run.json`
- `submit_real_project_dry_run.json`
- `packet_validation.json`
- `observability_verdict.txt`
- `evidence_manifest.json`

## Escalation Triggers

- The guard suppresses missing dependency warnings for changed accepted source hashes.
- A ready or nonterminal packet with missing dependencies becomes runnable.
- Real-project dry-run mutates runtime registry state.
- Packet validation or targeted regression tests fail.
