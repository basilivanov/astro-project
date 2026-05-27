# Execution Packet: FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION-W01-PIPELINE-TASKS-SPLIT

## Objective

Split Prefect task wrappers out of `prefect_grace/flows/feature_pipeline.py`
into bounded `prefect_grace/flows/pipeline_tasks/` modules without changing
runtime behavior.

The previous helper-only split moved pure/read-only helper logic. This packet
is the next mechanical extraction: decorated `@task` wrappers move into task
modules, while `feature_pipeline.py` remains the facade and keeps the public
flow entrypoints.

This packet must not rewrite the large `feature_pipeline()` body. Flow-body
phase extraction is deferred to a later packet.

## Slice

- slice_id: `SLICE-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION`
- slice_slug: `grace-feature-pipeline-task-extraction`
- feature_id: `FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION`
- packet_id: `FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION-W01-PIPELINE-TASKS-SPLIT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT-W01-FEATURE-PIPELINE-MODULE-SPLIT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION`

## Source Of Truth

- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT/EXECUTION_PACKET.md`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_module_split.py`

## Impacted Modules

- `M-GRACE-FEATURE-PIPELINE`
- `M-GRACE-PIPELINE-TASKS`
- `M-GRACE-PIPELINE-HELPERS`
- `M-GRACE-PREFECT-FLOW-FACADE`

## Required Design Decisions

### 1. Task Extraction Only

Move decorated Prefect task wrappers into:

```text
prefect_grace/flows/pipeline_tasks/
  __init__.py
  bootstrap_tasks.py
  planner_tasks.py
  architect_tasks.py
  execution_tasks.py
  review_tasks.py
  wave_tasks.py
  artifact_tasks.py
  canon_tasks.py
```

`feature_pipeline.py` must continue to expose the old task names by importing
them from the new task modules.

### 2. Flow Entry Points Stay In The Facade

Do not move:

- `feature_pipeline`;
- `review_router_flow`.

Their `@flow` names and `flow_run_name` templates must stay byte-identical.

### 3. Preserve Prefect Task Semantics

For every moved task, preserve:

- function name;
- decorator type;
- `task_run_name`;
- parameters and return shape;
- logging behavior;
- state write behavior;
- artifact publication behavior;
- monkeypatch compatibility where existing tests patch through
  `prefect_grace.flows.feature_pipeline`.

### 4. Do Not Extract Flow Body Phases Yet

The large body of `feature_pipeline()` remains in `feature_pipeline.py`.
Do not create phase runner modules in this packet.

### 5. GRACE Contracts For New Task Modules

Every new `pipeline_tasks/*.py` module must have:

- `AI_HEADER`;
- module contract;
- module map;
- function contracts for public task wrappers.

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/__init__.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/bootstrap_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/planner_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/architect_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/execution_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/review_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/wave_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/artifact_tasks.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/canon_tasks.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_module_split.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/**`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`

## Must Preserve

- Existing imports from `prefect_grace.flows.feature_pipeline` keep working.
- `feature_pipeline.py` remains the public facade and flow entrypoint.
- `feature_pipeline` and `review_router_flow` remain in `feature_pipeline.py`.
- Task and flow names remain byte-identical.
- `task_run_name` and `flow_run_name` templates remain byte-identical.
- No product backend/frontend files are modified.
- No live agents, Prefect deployments, Docker, backend, frontend, or Playwright
  are started by tests.
- No runtime state under `prefect_grace/state/*.yaml` is mutated.

## Required Implementation Shape

1. Record pre/post decorated inventory for logical task and flow names.
2. Move task wrappers into the target `pipeline_tasks/` modules by domain.
3. Import the moved tasks back into `feature_pipeline.py`.
4. Preserve facade-level monkeypatch points where existing tests patch through
   `prefect_grace.flows.feature_pipeline`.
5. Keep `feature_pipeline()` and `review_router_flow()` in the facade.
6. Add or extend tests proving facade imports and task/flow inventory are
   stable.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_feature_pipeline_module_split.py \
  tests/test_prefect_grace_synthetic_edge_matrix.py
```

Run platform regressions:

```bash
pytest -q \
  tests/test_prefect_grace_codex_launcher.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py \
  tests/test_prefect_grace_rework_resume_policy.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_backlog_controller_rework.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/flows
python3 scripts/grace_lint.py prefect_grace/flows/feature_pipeline.py
python3 scripts/grace_lint.py prefect_grace/flows/pipeline_tasks
python3 scripts/grace_lint.py prefect_grace/flows/pipeline_helpers
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION/EXECUTION_PACKET.md \
  --strict --json
```

Run size check as informational evidence:

```bash
python3 scripts/check_size_limits.py --root prefect_grace/flows
```

The size check is not a hard gate for this packet because the large
`feature_pipeline()` body is intentionally deferred to a later flow-body
extraction packet.

## Expected Evidence

- Targeted pytest output.
- Platform regression pytest output.
- Compile output.
- Targeted lint output for `feature_pipeline.py`, `pipeline_tasks`, and
  `pipeline_helpers`.
- Strict validation output for this `EXECUTION_PACKET.md`.
- Before/after line counts.
- Before/after decorated task/flow inventory.
- Import compatibility proof.
- Note for whole-flows lint/size degradation if it is caused only by known
  deferred debt.

## Escalation Triggers

- A task name or run-name template must change.
- A flow entrypoint must move.
- The `feature_pipeline()` body must be split to complete this packet.
- Existing monkeypatch/import compatibility cannot be preserved.
- Product backend/frontend files need changes.
- `codex_launcher.py` or platform modules need changes.
- Synthetic matrix or feature pipeline regressions fail.

## Reviewer Gate

Reviewer must reject this packet if:

- any task or flow name changes;
- `feature_pipeline` or `review_router_flow` moves out of `feature_pipeline.py`;
- compatibility imports from `prefect_grace.flows.feature_pipeline` break;
- behavior changes are mixed with extraction;
- product files, runtime state, or launcher/platform internals are modified;
- targeted feature pipeline or synthetic matrix tests fail;
- the packet lacks strict validation evidence.
