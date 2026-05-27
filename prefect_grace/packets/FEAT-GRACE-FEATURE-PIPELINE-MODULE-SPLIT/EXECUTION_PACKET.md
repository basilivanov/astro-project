# Execution Packet: GRACE Feature Pipeline Module Split

## Objective

Split pure helper logic out of `prefect_grace/flows/feature_pipeline.py`
without changing runtime behavior. The current file is a large state machine:
3199 lines, 78 top-level symbols, and a 1132-line `feature_pipeline()` flow
body. Moving both helpers and Prefect tasks in one attempt is too broad.
Therefore this packet is a helper-only extraction with compatibility aliases
and regression tests.

This packet must run only after the source-hash resume gate and synthetic edge
matrix are accepted. The goal is maintainability, not new orchestration
behavior.

## Slice

- slice_id: `SLICE-GRACE-FEATURE-PIPELINE-MODULE-SPLIT`
- slice_slug: `grace-feature-pipeline-module-split`
- feature_id: `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT`
- packet_id: `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT-W01-FEATURE-PIPELINE-MODULE-SPLIT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

## Impacted Modules

- `M-GRACE-FEATURE-PIPELINE`
- `M-GRACE-PIPELINE-HELPERS`
- `M-GRACE-REWORK-ROUTING`
- `M-GRACE-WAVE-PROGRESSION`
- `M-GRACE-EVIDENCE-COLLECTION`

## Recommended Role Assignment

- coder: `Sonnet high` or `Codex high`; this is helper extraction, not task extraction.
- verifier: `Codex medium`; must run synthetic matrix and feature pipeline regressions.
- reviewer: `Opus` or `Codex xhigh`; reviewer must focus on behavior preservation.
- rework policy: fresh session for failed behavior preservation tests; light resume only for import/name fixes.

## Required Design Decisions

### 1. Helper-Only Extraction Refactor

No new feature behavior is allowed. The diff must be explainable as:

- move pure/helper functions into modules;
- import them back into `feature_pipeline.py`;
- keep existing public names available;
- preserve task names, tags, Prefect run naming, and JSON outputs.

This packet must not move any function decorated with `@task` or `@flow`.
Prefect task extraction is deferred to a later packet after this packet and
the synthetic matrix are green.

This packet must also not move state-mutating helpers. A helper is state-mutating
if it calls or directly wraps any of:

- `update_record`, `mark_feature_status`, `create_packet`, `sync_packet_file`;
- `write_text`, `record_*`, `publish_*`, `notify_*`;
- live agent, Prefect artifact, Telegram, or filesystem write operations.

Examples that must remain in `feature_pipeline.py` in this packet:

- `_final_failure`;
- `_post_acceptance_final_status`;
- `_persist_wave_progression`;
- `_set_wave_progression_status`;
- `_build_direct_rework_followup_packets`;
- `_build_architect_direct_rework`;
- `_build_light_resume_followup`;
- any `@task` / `@flow` decorated function.

### 2. Target Module Layout

Target layout:

```text
prefect_grace/flows/
  feature_pipeline.py
  pipeline_helpers/
    __init__.py
    wave_progression.py
    rework_routing.py
    evidence_collector.py
    status_formatter.py
    normalizers.py
```

Out of scope for this packet and reserved for a later packet:

```text
prefect_grace/flows/pipeline_tasks/
  bootstrap_tasks.py
  planner_tasks.py
  architect_tasks.py
  execution_tasks.py
  review_tasks.py
  wave_tasks.py
  artifact_tasks.py
  canon_tasks.py
```

If the helper split is still too large for one safe attempt, the coder must
stop and propose a smaller wave. Do not partially move unrelated code just to
satisfy the layout.

### 3. Compatibility Aliases

`feature_pipeline.py` must continue to expose old helper names where tests or
callers depend on them:

```python
from prefect_grace.flows.pipeline_helpers.wave_progression import plan_wave_sequence

_plan_wave_sequence = plan_wave_sequence
```

Aliases may be temporary but must remain until all internal tests and imports
are migrated.

### 4. Preserve Prefect Semantics

Moving functions must not change:

- `@flow` names;
- `@task` names;
- task run names;
- deployment names;
- Prefect tags;
- artifact names;
- flow return JSON shape.

### 5. Size Guardrails

After refactor:

- `feature_pipeline.py` target for this helper-only packet: under 2600 lines;
- stretch target: under 2400 lines if it can be achieved without moving stateful helpers;
- final target under 800 lines belongs to the later Prefect task extraction packet;
- each new module target: under 600 lines;
- no new function above local size guardrails;
- no new catch-all helper module named `utils.py`.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/__init__.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/wave_progression.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/rework_routing.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/evidence_collector.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/status_formatter.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/normalizers.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_module_split.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT/**`

## Frozen Scope

- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/rework_resume_policy.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/solarsage-astro/**`
- `/opt/astro-project/prefect_grace/flows/pipeline_tasks/**`
- `/opt/astro-project/scripts/grace_lint.py`

## Must Preserve

- All existing feature pipeline tests pass.
- Synthetic edge matrix stays green.
- No product backend/frontend files are modified.
- No Codex launcher behavior changes.
- Existing imports from `prefect_grace.flows.feature_pipeline` continue working.
- No live agents or Prefect deployments are started by tests.
- No `@task` or `@flow` decorated function is moved in this packet.
- No Prefect task run name, flow name, tag, artifact key, or deployment name changes.
- No module import may create side effects beyond the current `feature_pipeline.py` import behavior.

## Required Implementation Shape

This packet contains only helper extraction. Execute in this order:

1. Record a baseline inventory of every existing `@task` and `@flow` name,
   task run name, flow run name, and public helper import consumed by tests.
2. Move normalizers and pure formatting helpers; run targeted regression tests.
3. Move read-only evidence/path extraction helpers; run targeted regression
   tests. Do not move helpers that load mutable state unless the state access is
   read-only and behavior is covered by fixtures.
4. Move pure wave progression planning helpers. Do not move persistence/status
   mutation helpers.
5. Move pure rework classification helpers. Do not move follow-up packet
   builders that create or update packet records.
6. Run the synthetic matrix and feature pipeline dynamic regressions.
7. Keep `feature_pipeline.py` as the unchanged flow/task entrypoint and
   compatibility facade.

Every moved function must retain:

- same behavior;
- same return shape;
- same error behavior;
- targeted regression coverage.

No moved helper may silently capture module globals differently. Imports,
constants, stores, paths, clock calls, and environment access used by a moved
helper must either remain equivalent or be passed explicitly without changing
observable behavior.

### Safety Assertions

Add or extend tests to assert:

- all existing `@task` and `@flow` exports remain in
  `prefect_grace.flows.feature_pipeline`;
- Prefect flow/task names and task run name templates are byte-identical to
  the pre-extraction baseline;
- compatibility aliases for moved underscore-prefixed helpers resolve and
  return unchanged results for representative fixtures;
- state-mutating helpers listed in this packet still live in
  `feature_pipeline.py`;
- synthetic matrix outcomes and CLI JSON envelope remain unchanged;
- importing any new helper module does not start a live agent, write registry
  state, or publish Prefect artifacts.

Evidence must include a before/after inventory for decorated functions. Any
change in that inventory is a blocker, even if tests are green.

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
python3 -m compileall prefect_grace/flows
python3 scripts/grace_lint.py prefect_grace/flows
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT/EXECUTION_PACKET.md \
  --strict --json
```

Run size check if available:

```bash
python3 scripts/check_size_limits.py --root prefect_grace/flows
```

This check is informational in this helper-only packet. The repo-wide
1000/4000 thresholds will still report the pre-existing oversized
`feature_pipeline.py` until the later task-extraction packet. Use the
output as a regression signal and capture before/after line counts in the
evidence; do not fail this packet solely because the global thresholds
remain exceeded.

## Expected Evidence

Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- test outputs;
- before/after line counts for `feature_pipeline.py` and new modules;
- import compatibility proof;
- list of moved functions by source and destination;
- baseline and post-refactor inventory of `@task` / `@flow` names, task run
  names, flow run names, tags, and artifact keys;
- confirmation that no decorated Prefect function moved out of
  `feature_pipeline.py`;
- confirmation that no state-mutating helper moved out of `feature_pipeline.py`;
- confirmation that no `codex_launcher.py` or product files changed.

## Escalation Triggers

Stop and ask controller if:

- a moved function requires behavior changes;
- a task name or Prefect artifact name must change;
- any `@task` or `@flow` decorated function appears necessary to move;
- any state-mutating helper appears necessary to move;
- extraction exceeds one safe packet;
- `codex_launcher.py` appears necessary to edit;
- synthetic matrix fails for a reason unrelated to imports.

## Reviewer Gate

Reviewer must reject this packet if:

- behavior changes are mixed with extraction;
- Prefect task/flow naming changes without explicit contract update;
- any decorated `@task` or `@flow` function moved in this helper-only packet;
- any state-mutating helper moved in this helper-only packet;
- compatibility imports break;
- synthetic edge matrix fails;
- `codex_launcher.py` or product files are modified;
- new modules become oversized.
