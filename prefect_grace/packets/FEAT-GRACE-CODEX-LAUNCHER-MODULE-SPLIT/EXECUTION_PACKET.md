# Execution Packet: GRACE Codex Launcher Module Split

## Objective

Split `prefect_grace/tasks/codex_launcher.py` into smaller modules after the
source-hash resume gate, synthetic edge matrix, and feature pipeline split are
accepted.

This packet is an extraction-only refactor of the Codex executor adapter. It
must not change resume behavior, prompt content, heartbeat behavior, process
execution, session storage, or registry semantics.

## Slice

- slice_id: `SLICE-GRACE-CODEX-LAUNCHER-MODULE-SPLIT`
- slice_slug: `grace-codex-launcher-module-split`
- feature_id: `FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT`
- packet_id: `FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT-W01-CODEX-LAUNCHER-MODULE-SPLIT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT-W01-FEATURE-PIPELINE-MODULE-SPLIT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher_resume_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

## Impacted Modules

- `M-GRACE-CODEX-LAUNCHER`
- `M-GRACE-CODEX-PROMPT-BUILDER`
- `M-GRACE-CODEX-PROCESS-RUNNER`
- `M-GRACE-CODEX-PROGRESS-TRACKER`
- `M-GRACE-CODEX-SESSION-MANAGER`
- `M-GRACE-CODEX-RESUME-POLICY`
- `M-GRACE-CODEX-COMMAND-BUILDER`

## Recommended Role Assignment

- coder: `Opus` or `Codex xhigh`; this is a critical executor adapter refactor.
- verifier: `Codex medium`; must run launcher tests and synthetic matrix.
- reviewer: `Opus` or `Codex xhigh`; reviewer must inspect exact behavior preservation.
- rework policy: fresh session for any resume/process behavior failure.

## Required Design Decisions

### 1. Do Not Do This Until Safety Nets Are Accepted

This packet must not start before these packets are accepted:

- `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP`;
- `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP`;
- `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT`.

The launcher is close to live agent execution. Refactor without synthetic
coverage is not allowed.

### 2. Extraction-Only Refactor

No behavior changes are allowed. The diff must be limited to:

- moving functions/classes to focused modules;
- importing them into `codex_launcher.py`;
- keeping `launch_codex_for_packet(...)` as the stable public entrypoint;
- preserving existing public imports with compatibility aliases.

### 3. Target Module Layout

Target layout:

```text
prefect_grace/tasks/
  codex_launcher.py
  codex_launcher_helpers/
    __init__.py
    prompt_builder.py
    process_runner.py
    progress_tracker.py
    session_manager.py
    resume_policy.py
    command_builder.py
```

`codex_launcher.py` remains the facade and should target under 500 lines.

### 4. Preserve Runtime Semantics

The split must preserve:

- exact command building;
- `codex exec` vs `codex resume` choice;
- source-hash resume gate behavior;
- auto-resume after stall/timeout;
- fresh retry on startup-only/no-output stall;
- heartbeat payload shape;
- thread id extraction;
- session storage;
- registry update of `last_executed_source_hash` and `latest_coder_session_id`;
- prompt content unless the change is byte-for-byte equivalent after normalization.

### 5. No Opportunistic Improvements

Do not add new prompt sections, wave labels, canon digest loading, model
changes, heartbeat fields, or unrelated launcher behavior. Those require
separate packets.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/__init__.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/prompt_builder.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/process_runner.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/progress_tracker.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/session_manager.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/resume_policy.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher_helpers/command_builder.py`
- `/opt/astro-project/scripts/grace_lint.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_codex_launcher.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher_resume_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher_module_split.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT/**`

## Frozen Scope

- `/opt/astro-project/prefect_grace/flows/**`
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

## Must Preserve

- `launch_codex_for_packet(...)` remains import-compatible.
- Existing launcher tests pass.
- Resume gate behavior remains unchanged.
- Synthetic edge matrix remains green.
- No live agents are started by tests.
- No product backend/frontend files are modified.
- No feature pipeline behavior changes.

## Required Implementation Shape

Suggested extraction order:

1. Move command builder helpers.
2. Move session manager helpers.
3. Move resume policy helpers.
4. Move progress tracker helpers.
5. Move process runner helpers.
6. Move prompt builder helpers last, because prompt drift is high risk.

After each move, run launcher tests before continuing.

Compatibility facade must keep:

```python
from prefect_grace.tasks.codex_launcher_helpers.prompt_builder import build_packet_prompt
from prefect_grace.tasks.codex_launcher_helpers.prompt_builder import role_prompt_for
```

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_codex_launcher.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py \
  tests/test_prefect_grace_codex_launcher_module_split.py
```

Run safety regressions:

```bash
pytest -q \
  tests/test_prefect_grace_synthetic_edge_matrix.py \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_rework_resume_policy.py
```

Run static checks:

```bash
python3 -m compileall prefect_grace/tasks
python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py prefect_grace/tasks/codex_launcher_helpers
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT/EXECUTION_PACKET.md \
  --strict --json
```

Run prompt/command drift checks:

```bash
pytest -q tests/test_prefect_grace_codex_launcher.py -k "command or prompt or resume"
```

## Expected Evidence

Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- test outputs;
- before/after line counts;
- moved function map;
- proof that command arrays for representative exec/resume cases did not change;
- proof that prompt snapshots or normalized prompt digests did not drift;
- confirmation that no `feature_pipeline.py` or product files changed.

## Escalation Triggers

Stop and ask controller if:

- prompt content must change;
- command building must change;
- resume behavior must change;
- process runner behavior must change;
- extraction exceeds one safe packet;
- synthetic matrix fails for a behavior reason.

## Reviewer Gate

Reviewer must reject this packet if:

- any behavior change is mixed with extraction;
- `codex exec` or `codex resume` command arrays drift unexpectedly;
- source-hash resume gate weakens;
- heartbeat/session/process semantics change;
- synthetic edge matrix fails;
- `feature_pipeline.py` or product files are modified;
- new helper modules are oversized or named as catch-all `utils.py`.

