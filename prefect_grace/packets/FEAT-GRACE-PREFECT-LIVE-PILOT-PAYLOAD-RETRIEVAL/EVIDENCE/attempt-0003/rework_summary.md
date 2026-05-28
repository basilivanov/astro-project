# Rework Summary: runtime root plumbing

## Runtime Gate Progress
The previous rework fixed stale Prefect idempotency. Reviewer runtime verification created fresh flow run `c9505e87-23b3-4dcd-b7a2-147dd3fa9e11`; the worker started, the flow completed, and the status reader read the managed payload from file.

## New Runtime Blocker
The managed payload reported `domain_status=runner_error`, `scope_verdict=evidence_incomplete`, and `live_agents_started=0`. Code inspection showed the managed Prefect flow did not pass the synthetic runtime state root or synthetic repo root into the launcher path:

- `managed_packet_runner_flow()` called `run_managed_packet()` without `runtime_state_root`.
- `run_managed_packet()` only passed `runtime_state_root` to `launch_codex_for_packet()` when a `project` object existed.
- Prefect managed flow has no `project` object, so launcher packet lookup fell back to default `/opt/astro-project` roots instead of the synthetic temp registry/repo.

## Fix
- Added optional `runtime_state_root` to managed packet flow parameters.
- `_parameters_for_packet(... runner_kind="managed")` now passes `runtime_state_root`.
- `managed_packet_runner_flow()` and `run_managed_packet_task()` accept and forward `runtime_state_root`.
- `run_managed_packet()` accepts explicit `runtime_state_root` and forwards it to launcher even when no project object exists.
- `run_managed_packet()` forwards its `repo_root` as `project_root` to the launcher.
- `launch_codex_for_packet()` accepts optional `project_root` and uses it for registry packet path resolution and prompt path normalization, preserving default `ROOT_DIR` behavior when absent.

## Runtime Scope
No real live Prefect pilot was run by worker-coder during this rework. This attempt addresses the reviewer-observed fresh-run `runner_error` by unit/contract coverage of the missing root plumbing.
