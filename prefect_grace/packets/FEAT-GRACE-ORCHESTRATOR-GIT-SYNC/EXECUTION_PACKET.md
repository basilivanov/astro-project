# Execution Packet: FEAT-GRACE-ORCHESTRATOR-GIT-SYNC-W01-AUTO-BRANCHING

## Objective

Implement auto-branching and git-sync logic for the GRACE orchestration platform.
The git-sync logic must automatically isolate execution in git worktrees and branches,
and automatically commit and push changes to the remote repository when a packet is accepted.

## Slice

- slice_id: `SLICE-GRACE-ORCHESTRATOR-GIT-SYNC`
- slice_slug: `grace-orchestrator-git-sync`
- feature_id: `FEAT-GRACE-ORCHESTRATOR-GIT-SYNC`
- packet_id: `FEAT-GRACE-ORCHESTRATOR-GIT-SYNC-W01-AUTO-BRANCHING`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER-W01-BACKLOG-CONTROLLER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-GIT-SYNC`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/git_sync.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_sync.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/packet_registry.yaml`
- `/opt/astro-project/prefect_grace/state/packet_registry.yaml`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-GIT-SYNC/**`
- `/opt/astro-project/tests/test_prefect_grace_git_sync.py`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/platform/**` outside allowed scope
- `/opt/astro-project/prefect_grace/packets/**` outside allowed scope

## Must Preserve

- Isolated packet worktree branches must use the format: `agent/<project_key>/<packet_id>/attempt-<NNNN>`.
- Real git commits and pushes must only occur when a packet is explicitly accepted and apply flag is set.
- All actions must support dry-run by default.
- CLI output must support JSON serialization matching the standard grace CLI envelope.

## Verification

Run targeted unit tests:
```bash
pytest -q tests/test_prefect_grace_git_sync.py
```
