# Execution Packet: FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT-W01-FLOW-PHASE-RUNNERS

## Objective

Split the large `feature_pipeline()` flow body in
`prefect_grace/flows/feature_pipeline.py` into bounded plain-Python phase
runner modules without changing runtime behavior.

The previous packets already extracted pure helpers and decorated Prefect task
wrappers. After those packets, `feature_pipeline.py` is still oversized:

- `feature_pipeline.py`: 1826 physical lines;
- `feature_pipeline()`: 1132 AST lines and 6255 tokens;
- only `feature_pipeline` and `review_router_flow` should remain as decorated
  flow entrypoints in the facade.

This packet is the flow-body extraction step. It must make the size check pass
for `prefect_grace/flows` by reducing the facade and the `feature_pipeline()`
function body, while keeping all task/flow names, task/flow run-name templates,
state transitions, artifact publication points, and return dictionaries
compatible with the current behavior.

## Slice

- slice_id: `SLICE-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT`
- slice_slug: `grace-feature-pipeline-flow-body-split`
- feature_id: `FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT`
- packet_id: `FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT-W01-FLOW-PHASE-RUNNERS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION-W01-PIPELINE-TASKS-SPLIT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/**`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-TASK-EXTRACTION/EXECUTION_PACKET.md`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_module_split.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

## Impacted Modules

- `M-GRACE-FEATURE-PIPELINE`
- `M-GRACE-PIPELINE-PHASES`
- `M-GRACE-PIPELINE-TASKS`
- `M-GRACE-PIPELINE-HELPERS`
- `M-GRACE-PREFECT-FLOW-FACADE`
- `M-GRACE-WAVE-PROGRESSION`
- `M-GRACE-REWORK-ROUTING`

## Recommended Role Assignment

- coder: `Codex high` or `Sonnet high`; this is a behavior-preserving
  extraction of stateful orchestration code.
- verifier: `Codex medium`; must run the feature pipeline profile, synthetic
  matrix, static checks, and post-test evidence review.
- reviewer: `Opus` or `Codex xhigh`; reviewer must focus on branch parity,
  monkeypatch compatibility, and unchanged result envelopes.
- rework policy: fresh session for behavior or state-transition regressions;
  light resume only for lint, imports, or packet evidence fixes.

## Required Design Decisions

### 1. Flow Entry Points Stay In The Facade

Do not move or rename:

- `feature_pipeline`;
- `review_router_flow`.

Their decorators must remain byte-identical:

```python
@flow(name="prefect-grace-feature-pipeline", flow_run_name="feature:{feature_id}")
@flow(name="prefect-grace-review-router", flow_run_name="review:{packet_id}:{verdict}")
```

`feature_pipeline.py` remains the public compatibility facade. Existing imports
from `prefect_grace.flows.feature_pipeline` must continue to work.

### 2. Extract Plain Phase Runners, Not New Prefect Units

Create bounded plain-Python modules under:

```text
prefect_grace/flows/pipeline_phases/
  __init__.py
  context.py
  bootstrap_phase.py
  planning_phase.py
  wave_execution_phase.py
  wave_role_handlers.py
  finalization_phase.py
```

The exact internal helper names may differ, but the responsibilities must stay
clear:

- `context.py`: small dataclasses or typed dict helpers for shared runtime
  state and dependency injection.
- `bootstrap_phase.py`: seed feature packets, mark in-progress, initialize
  packet result state, run optional canon digest preflight.
- `planning_phase.py`: run/skip architect, resolve/write architect artifacts,
  run/skip planner, resolve/materialize/validate planner contract, build and
  persist wave progression.
- `wave_execution_phase.py`: execute wave queues, dependency retry/deadlock
  handling, queue mutation, wave status updates.
- `wave_role_handlers.py`: bounded role handlers for coder, verifier,
  reviewer, and architect wave gate branches.
- `finalization_phase.py`: required-wave completion checks, accepted feature
  finalization, final artifact publication, and final return envelope.

No new `@task` or `@flow` decorators are allowed in `pipeline_phases`.

### 3. Preserve Monkeypatch Compatibility

Existing tests patch symbols through `prefect_grace.flows.feature_pipeline`, for
example:

- `launch_codex_for_packet`;
- `publish_feature_artifacts`;
- `record_review`;
- `mark_packet_status_task`;
- `notify_packet_event`;
- `find_record`;
- `get_run_logger`.

Phase modules must not bypass those facade patch points by binding direct
imports at module import time. Use one of these patterns:

- build a small dependency object inside `feature_pipeline()` from the facade's
  current globals and pass it to phase runners;
- or pass the needed callables explicitly as keyword arguments.

Do not import `prefect_grace.flows.feature_pipeline` from phase modules. Avoid
circular imports and avoid wildcard imports.

### 4. Preserve Runtime Branch Semantics

Every branch in the current `feature_pipeline()` body must keep the same
observable behavior:

- canon digest failure returns `environment_blocked` with
  `inspect-failed-canon-digest`;
- architect failure returns `environment_blocked` with
  `inspect-failed-architect`;
- architect `requires_user_decision` returns `awaiting_architect`;
- planner failure returns `environment_blocked` with `inspect-failed-planner`;
- invalid planner output returns `pipeline_invalid`;
- invalid wave progression returns `fix-wave-plan-continuation`;
- dependency deadlock returns `dependency-deadlock:<packet_id>`;
- missing verifier/reviewer/rework packet branches keep their current
  `next_action` values;
- reviewer accepted/rework/escalate/blocked branches keep current status
  updates, requeue behavior, and artifact publication points;
- architect wave accepted/rework/blocked branches keep current status updates,
  notifications, and return envelope;
- final acceptance returns `awaiting_commit` with candidate commit evidence.

Scripted fallback indexes for `reviewer_verdict_script`,
`review_reasons_script`, `wave_verdict_script`, and `wave_reasons_script` must
advance exactly as they do now.

### 5. Preserve Prefect Semantics

Calling extracted phase runners from inside `feature_pipeline()` must preserve:

- Prefect task invocation order;
- `with tags(...)` scopes and tag strings;
- task and flow run-name templates;
- artifact publication timing;
- dry-run behavior;
- live-agent behavior gates;
- exception/return behavior.

Phase runners are ordinary Python functions executed inside the existing flow
context. Do not introduce subflows, deployments, workers, async execution,
threads, or background queues.

### 6. Size Check Becomes A Hard Gate

Unlike the helper/task extraction packets, this packet must make the local size
check pass for the changed flow package:

```bash
python3 scripts/check_size_limits.py --root prefect_grace/flows
```

Targets:

- `prefect_grace/flows/feature_pipeline.py`: under 1000 physical lines;
- `feature_pipeline()`: under 4000 tokens;
- every new `pipeline_phases/*.py` module: under 1000 physical lines;
- every new public phase runner function: under 4000 tokens.

If the full wave execution loop cannot be split safely in one attempt, stop and
write a smaller follow-up packet before making partial behavior changes.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/__init__.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/context.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/bootstrap_phase.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/planning_phase.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/wave_execution_phase.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/wave_role_handlers.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_phases/finalization_phase.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_module_split.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_flow_body_split.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/**`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/scripts/check_size_limits.py`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`

## Must Preserve

- Existing imports from `prefect_grace.flows.feature_pipeline` keep working.
- `feature_pipeline` and `review_router_flow` remain in `feature_pipeline.py`.
- No task wrapper is moved out of `pipeline_tasks`.
- No pure helper is moved out of `pipeline_helpers`.
- No product backend/frontend files are modified.
- No live agents, Prefect deployments, Docker, backend, frontend, or Playwright
  are started by tests.
- No runtime state under `prefect_grace/state/*.yaml` is mutated.
- Public result dictionaries preserve existing keys and branch-specific values.
- All existing feature pipeline dynamic scenarios remain green.
- Synthetic edge matrix remains green.
- Whole-flows lint debt in unrelated modules must not be expanded.

## Required Implementation Shape

1. Record baseline evidence:
   - physical line count for `feature_pipeline.py`;
   - `feature_pipeline()` AST line span and token count;
   - decorated task/flow inventory across `feature_pipeline.py` and
     `pipeline_tasks`;
   - current targeted test profile status.
2. Add `pipeline_phases` package with module contracts, module maps, and
   function contracts.
3. Add a small runtime context/dependency shape. Keep it explicit and typed.
   Do not introduce a generic orchestration framework.
4. Move the initial seeding/canon-digest logic into a bootstrap phase runner.
   Run targeted feature pipeline tests.
5. Move architect/planner/materialization/wave-progression setup into a
   planning phase runner. Run targeted feature pipeline tests.
6. Split the wave loop into a wave execution runner and role handlers. Role
   handlers must stay small enough for size limits and must keep queue/rework
   semantics unchanged. Run targeted feature pipeline tests.
7. Move final required-wave and acceptance logic into a finalization runner.
   Run targeted feature pipeline tests.
8. Leave `feature_pipeline()` as a readable facade that builds dependencies,
   calls phase runners, and returns the same final dictionaries.
9. Extend tests to prove:
   - `feature_pipeline.py` still has only the two flow decorators;
   - `pipeline_phases` modules define no Prefect tasks or flows;
   - `pipeline_phases` modules do not import `prefect_grace.flows.feature_pipeline`;
   - facade monkeypatch points still affect phase behavior;
   - size check passes.
10. Run all verification commands and write bounded evidence under this packet.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_feature_pipeline_module_split.py \
  tests/test_prefect_grace_feature_pipeline_flow_body_split.py \
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
python3 scripts/grace_lint.py prefect_grace/flows/pipeline_phases
python3 scripts/grace_lint.py prefect_grace/flows/pipeline_tasks
python3 scripts/grace_lint.py prefect_grace/flows/pipeline_helpers
python3 scripts/check_size_limits.py --root prefect_grace/flows
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT/EXECUTION_PACKET.md \
  --strict --json
```

Run controller dry-runs after evidence is written:

```bash
python3 -m prefect_grace.cli bootstrap-backlog --dry-run --json
python3 -m prefect_grace.cli sync-packets --dry-run --json
```

Whole `python3 scripts/grace_lint.py prefect_grace/flows` may remain
degraded only for pre-existing unrelated contract debt in `live_dashboard.py`
and `packet_lifecycle.py`. It must not report new `feature_pipeline.py` or
`pipeline_phases` findings.

## Expected Evidence

- Targeted pytest output.
- Platform regression pytest output.
- Compile output.
- Targeted lint output for `feature_pipeline.py`, `pipeline_phases`,
  `pipeline_tasks`, and `pipeline_helpers`.
- Size check output showing no blocking violations under `prefect_grace/flows`.
- Strict packet validation output.
- Bootstrap/sync dry-run summaries.
- Before/after line counts.
- Before/after `feature_pipeline()` AST span and token count.
- Before/after decorated task/flow inventory.
- Import compatibility proof.
- Monkeypatch compatibility proof for facade-level patch points.
- Post-test observability verdict:
  `clean`, `degraded-but-expected`, `unexpected-degradation`, or
  `no-evidence-blocker`.

## Escalation Triggers

- A task or flow decorator must move.
- A task or flow name, `task_run_name`, or `flow_run_name` must change.
- A phase module needs to import `prefect_grace.flows.feature_pipeline`.
- Existing facade monkeypatch compatibility cannot be preserved.
- Result dictionary shape changes in any tested branch.
- A status transition, wave progression update, or artifact publication point
  changes.
- Size check cannot be made green without changing behavior.
- Product backend/frontend files need changes.
- `codex_launcher.py`, `pipeline_tasks`, `pipeline_helpers`, platform modules,
  or state files need behavior changes.
- Synthetic matrix or feature pipeline regressions fail.

## Reviewer Gate

Reviewer must reject this packet if:

- `feature_pipeline` or `review_router_flow` moves out of `feature_pipeline.py`;
- any decorated task/flow inventory entry changes;
- phase modules add Prefect decorators or subflows;
- phase modules bypass existing facade monkeypatch points;
- branch-specific `final_status`, `review_routes`, `wave_routes`, or
  `verification_records` shapes change;
- size check under `prefect_grace/flows` still fails because of
  `feature_pipeline.py` or the new phase modules;
- product files, runtime state, launcher internals, helper modules, or task
  modules are modified outside the allowed scope;
- targeted feature pipeline or synthetic matrix tests fail;
- the packet lacks strict validation and bounded evidence.
