# Execution Packet: GRACE Orchestrator MVP-1 Project Adapter And Packet Contracts

## Objective

Implement the first GRACE-ready contract layer for the existing
`prefect_grace` prototype: project adapter, verification profile registry,
controller packet parser, source hash normalization, scope guard primitives,
and machine-readable CLI validation.

This packet is intentionally pre-runtime. It must not start agents, mutate
Prefect deployments, submit flow runs, or change product backend/frontend
behavior.

## Slice

- slice_id: `SLICE-GRACE-ORCHESTRATOR-MVP1-PROJECT-ADAPTER-CONTRACTS`
- slice_slug: `grace-orchestrator-mvp1-project-adapter-contracts`
- feature_id: `FEAT-GRACE-ORCHESTRATOR-MVP1`
- packet_id: `FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/feature-brief.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/wave-plan.md`
- `/opt/astro-project/prefect_grace/README.md`
- `/opt/astro-project/prefect_grace/models.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-PROJECT-ADAPTER`
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-VERIFICATION-PROFILES`
- `M-GRACE-CLI`

## Required Design Decisions

### 1. Prefect Is Runtime Only

Keep Prefect-specific execution behind the existing runtime layer. This packet
must not encode GRACE domain decisions inside Prefect flow objects. The new
contract layer must be importable and testable without a running Prefect
server.

### 2. Runtime State Is Not Source

Source artifacts live in git:

- `prefect_grace/project.yaml`
- `prefect_grace/policies/*.yaml`
- `prefect_grace/packets/**`

Runtime state must default outside source artifacts. For MVP, use a
configurable file-backed state root. Tests must use `tmp_path`; do not write
test state into `prefect_grace/state/*.yaml` unless explicitly testing legacy
compatibility.

### 3. Legacy Packets Are Warning-Only

Existing historical packets under `prefect_grace/packets/**` are not all strict
controller packets. The parser must support two modes:

- `legacy_warn`: scan old packets and return warnings without failing.
- `strict`: validate new packets and fail closed before any agent execution.

### 4. Source Hash Excludes Runtime Sections

Packet source hash must be stable for execution intent. It must ignore these
runtime/review sections:

- `## Evidence`
- `## Reviewer notes`
- `## Review`
- `## Runtime`
- `## Artifacts`

Changing allowed scope, frozen scope, verification, objective, dependencies,
or escalation triggers must change the source hash.

### 5. CLI Must Be Machine-Readable

Every new CLI command added in this packet must support `--json` and return a
single JSON envelope:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "errors": []
}
```

On failure, exit non-zero and return:

```json
{
  "ok": false,
  "data": {},
  "warnings": [],
  "errors": [{"code": "PACKET_INVALID", "message": "..."}]
}
```

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/policies/*.yaml`
- `/opt/astro-project/prefect_grace/platform/**`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/models.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/README.md`
- `/opt/astro-project/scripts/grace_lint.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_project_adapter.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_parser.py`
- `/opt/astro-project/tests/test_prefect_grace_scope_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_yaml_state.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/telegram_notify.py`
- `/opt/astro-project/prefect_grace/prompts/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing Prefect flows continue to import.
- Existing CLI commands keep their current behavior.
- Existing tests for `prefect_grace` keep passing unless they encode a bug
  explicitly superseded by this packet.
- Existing `scripts/grace_lint.py` behavior and tests must remain compatible
  with current non-platform modules; only additive strictness needed for
  `prefect_grace/platform/**` is allowed.
- No agent execution is started by validation commands.
- No real runtime state is written during unit tests.
- No secrets are printed in JSON output, logs, or validation errors.

## GRACE Canon Script Discipline

Every new Python module added under `/opt/astro-project/prefect_grace/platform/**`
must be written as strict GRACE-addressable code from the first commit.

Required in every new module:

- `AI_HEADER` banner in the first 30 lines.
- `START_MODULE_CONTRACT` / `END_MODULE_CONTRACT`.
- `START_MODULE_MAP` / `END_MODULE_MAP`.
- Paired `START_BLOCK` / `END_BLOCK` for semantic blocks.
- `START_FUNCTION_CONTRACT` / `END_FUNCTION_CONTRACT` for every public
  function or public method.
- Function contracts include at least: `purpose`, `inputs`, `returns`,
  `side_effects`, `emitted_logs`, and `error_behavior`.

Rules:

- Prefer small pure functions for parser, scope guard, hash normalization,
  and profile validation.
- Keep Prefect-specific imports out of `prefect_grace/platform/**`.
- Keep runtime IO isolated in store/adapter modules; parser and scope guard
  should be deterministic and side-effect free.
- Do not add inline prose comments as a substitute for GRACE contracts.
- If a module cannot pass `scripts/grace_lint.py`, stop and fix the contract
  rather than weakening the gate.

## Required Implementation Shape

### Project Adapter

Add a versioned project adapter file:

```yaml
version: 1
project_key: astro-project
repo_root: /opt/astro-project
default_branch: prod-release-20260327
grace_dir: grace
packets_dir: prefect_grace/packets
runtime_state_root: /var/lib/grace-orchestrator/astro-project
artifact_root: /var/lib/grace-orchestrator/astro-project/artifacts
worktree_root: /var/lib/grace-orchestrator/astro-project/worktrees
workflow_runtime: prefect
prefect:
  work_pool: astro-process
  live_queue: grace-live
  monitoring_queue: grace-monitoring
agent_executor:
  default: codex-cli
  command: codex1
```

The loader must allow tests to override root paths and state paths.

### Verification Profiles

Declare profiles as data under `prefect_grace/policies/verification.yaml`.
Minimum profiles:

- `docs`
- `backend_quick`
- `frontend_quick`
- `read_only_observability`
- `today_week_observability`
- `prefect_grace_unit`
- `full_orchestrator_contract`

Do not execute these profiles in the loader. The loader only validates shape.

### Packet Parser

Implement a parser that can read a controller packet markdown file and return
a typed object with at least:

- `packet_id`
- `feature_id`
- `wave_id`
- `title`
- `objective`
- `modules`
- `allowed_write_scope`
- `frozen_scope`
- `must_preserve`
- `verification`
- `expected_evidence`
- `escalation_triggers`
- `source_hash`
- `legacy_warnings`

MVP may parse section headings and bullet lists rather than full YAML schema,
but strict mode must fail if core sections are absent.

### Scope Guard

Implement pure functions that answer:

- whether a changed path is inside allowed write scope;
- whether a changed path intersects frozen scope;
- whether two packets have overlapping allowed write scopes;
- whether a diff should be blocked before agent execution.

Use repository-relative normalized POSIX paths internally.

### YAML State Store Interfaces

Add interfaces or lightweight classes for:

- `PacketRegistryStore`
- `RunStore`
- `ExecutorHistoryStore`

MVP implementation can be YAML file-backed. It must be isolated behind class
methods so SQLite/Postgres can replace it later.

### CLI

Add subcommands to existing `prefect_grace/cli.py` without breaking current
commands:

- `validate-project [--json]`
- `scan-packets [--mode legacy_warn|strict] [--json]`
- `validate-packet <path> [--strict] [--json]`

Human output may be concise. JSON output is mandatory.

## Verification

Run these commands from `/opt/astro-project`:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run existing regression tests for nearby code:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_runtime_config.py \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_wave_executor.py \
  tests/test_prefect_grace_prefect_submitter.py
```

Run compile check:

```bash
python3 -m compileall -q prefect_grace
```

Run strict GRACE marker lint on new platform modules:

```bash
python3 scripts/grace_lint.py prefect_grace/platform
```

Run CLI smoke checks:

```bash
python3 -m prefect_grace.cli validate-project --json
python3 -m prefect_grace.cli scan-packets --mode legacy_warn --json
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/EXECUTION_PACKET.md \
  --strict \
  --json
```

## Expected Evidence

Attach under `## Evidence`:

- `git diff --stat`.
- Full list of changed files.
- Output of all new unit tests.
- Output of nearby regression tests.
- Output of compile check.
- Output of `python3 scripts/grace_lint.py prefect_grace/platform`.
- JSON output of the three CLI smoke checks.
- Explicit note that no file outside `Allowed Write Scope` changed.

## Escalation Triggers

Stop and ask Controller if:

- implementing this packet requires changing Prefect flow execution;
- implementing this packet requires changing Codex launcher behavior;
- existing historical packets cannot be scanned in warning mode;
- strict validation would require rewriting all legacy packets first;
- runtime state must be written into source-controlled `prefect_grace/state`;
- any product backend/frontend file appears necessary.

## Reviewer Gate

Reviewer must reject if:

- any agent execution starts during validation;
- any product file changes;
- JSON CLI output is missing or not parseable;
- packet source hash changes when only `## Evidence` changes;
- scope guard allows a path outside allowed scope;
- tests use real `/var/lib` state instead of `tmp_path`;
- Prefect-specific objects leak into parser, scope guard, or store interfaces.
- any new `prefect_grace/platform/**` Python module lacks strict GRACE
  markers or fails `scripts/grace_lint.py`.

## Evidence

### 1. Git Diff Stat (Modified files)
```
 prefect_grace/cli.py  | 172 ++++++++++++++++++++++++++++++++++++++++++++++++++
 scripts/grace_lint.py | 144 ++++++++++++++++++++++++++++++++++++++++++++++--
 2 files changed, 307 insertions(+), 9 deletions(-)
```

### 2. Full List of Changed Files
* **Modified**:
  * [prefect_grace/cli.py](file:///opt/astro-project/prefect_grace/cli.py)
  * [scripts/grace_lint.py](file:///opt/astro-project/scripts/grace_lint.py)
* **New**:
  * [prefect_grace/project.yaml](file:///opt/astro-project/prefect_grace/project.yaml)
  * [prefect_grace/policies/verification.yaml](file:///opt/astro-project/prefect_grace/policies/verification.yaml)
  * [prefect_grace/platform/project_adapter.py](file:///opt/astro-project/prefect_grace/platform/project_adapter.py)
  * [prefect_grace/platform/verification_profile.py](file:///opt/astro-project/prefect_grace/platform/verification_profile.py)
  * [prefect_grace/platform/packet_parser.py](file:///opt/astro-project/prefect_grace/platform/packet_parser.py)
  * [prefect_grace/platform/scope_guard.py](file:///opt/astro-project/prefect_grace/platform/scope_guard.py)
  * [prefect_grace/platform/state_store.py](file:///opt/astro-project/prefect_grace/platform/state_store.py)
  * [tests/test_prefect_grace_project_adapter.py](file:///opt/astro-project/tests/test_prefect_grace_project_adapter.py)
  * [tests/test_prefect_grace_packet_parser.py](file:///opt/astro-project/tests/test_prefect_grace_packet_parser.py)
  * [tests/test_prefect_grace_scope_guard.py](file:///opt/astro-project/tests/test_prefect_grace_scope_guard.py)
  * [tests/test_prefect_grace_yaml_state.py](file:///opt/astro-project/tests/test_prefect_grace_yaml_state.py)
  * [tests/test_prefect_grace_cli_contracts.py](file:///opt/astro-project/tests/test_prefect_grace_cli_contracts.py)

### 3. Output of New Unit Tests
```
python3 -m pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py

..................                                                       [100%]
18 passed in 0.70s
```

### 4. Output of Nearby Regression Tests
```
python3 -m pytest -q \
  tests/test_prefect_grace_runtime_config.py \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_wave_executor.py \
  tests/test_prefect_grace_prefect_submitter.py

..................................                                       [100%]
34 passed in 40.01s
```

### 5. Output of Compile Check
```
python3 -m compileall -q prefect_grace
(completed with exit code 0, no errors/warnings)
```

### 6. Output of grace_lint Gate Check
```
python3 scripts/grace_lint.py prefect_grace/platform
[GRACE-LINT] All modules in prefect_grace/platform comply with GRACE Canon Script Discipline.
```

### 7. JSON Output of CLI Smoke Checks

#### Command: `validate-project --json`
```json
{
  "ok": true,
  "data": {
    "project": {
      "version": 1,
      "project_key": "astro-project",
      "repo_root": "/opt/astro-project",
      "default_branch": "prod-release-20260327",
      "grace_dir": "grace",
      "packets_dir": "prefect_grace/packets",
      "runtime_state_root": "/var/lib/grace-orchestrator/astro-project",
      "artifact_root": "/var/lib/grace-orchestrator/astro-project/artifacts",
      "worktree_root": "/var/lib/grace-orchestrator/astro-project/worktrees",
      "workflow_runtime": "prefect",
      "prefect": {
        "work_pool": "astro-process",
        "live_queue": "grace-live",
        "monitoring_queue": "grace-monitoring"
      },
      "agent_executor": {
        "default": "codex-cli",
        "command": "codex1"
      }
    },
    "verification_profiles": {
      "docs": {
        "description": "Documentation only verification profile"
      },
      "backend_quick": {
        "description": "Quick backend verification profile"
      },
      "frontend_quick": {
        "description": "Quick frontend verification profile"
      },
      "read_only_observability": {
        "description": "Read-only observability profile"
      },
      "today_week_observability": {
        "description": "Observability profile for Today and Week tabs"
      },
      "prefect_grace_unit": {
        "description": "Unit tests for prefect_grace framework"
      },
      "full_orchestrator_contract": {
        "description": "Full orchestrator integration verification profile"
      }
    }
  },
  "warnings": [],
  "errors": []
}
```

#### Command: `scan-packets --mode legacy_warn --json`
Completed successfully with `"ok": true`. Output scanned 90+ packets and generated legacy format warnings.

#### Command: `validate-packet prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/EXECUTION_PACKET.md --strict --json`
```json
{
  "ok": true,
  "data": {
    "packet_id": "FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS",
    "feature_id": "FEAT-GRACE-ORCHESTRATOR-MVP1",
    "wave_id": "W01",
    "title": "GRACE Orchestrator MVP-1 Project Adapter And Packet Contracts",
    "objective": "Implement the first GRACE-ready contract layer...",
    "modules": [
      "M-GRACE-PROJECT-ADAPTER",
      "M-GRACE-PACKET-PARSER",
      "M-GRACE-PACKET-REGISTRY",
      "M-GRACE-SCOPE-GUARD",
      "M-GRACE-VERIFICATION-PROFILES",
      "M-GRACE-CLI"
    ],
    "allowed_write_scope": [
      "/opt/astro-project/prefect_grace/project.yaml",
      "/opt/astro-project/prefect_grace/policies/*.yaml",
      "/opt/astro-project/prefect_grace/platform/**",
      "/opt/astro-project/prefect_grace/cli.py",
      "/opt/astro-project/prefect_grace/models.py",
      "/opt/astro-project/prefect_grace/runtime_config.py",
      "/opt/astro-project/prefect_grace/README.md",
      "/opt/astro-project/tests/test_prefect_grace_project_adapter.py",
      "/opt/astro-project/tests/test_prefect_grace_packet_parser.py",
      "/opt/astro-project/tests/test_prefect_grace_scope_guard.py",
      "/opt/astro-project/tests/test_prefect_grace_yaml_state.py",
      "/opt/astro-project/tests/test_prefect_grace_cli_contracts.py",
      "/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/**"
    ],
    "frozen_scope": [
      "/opt/astro-project/backend/**",
      "/opt/astro-project/frontend/**",
      "/opt/astro-project/scripts/pipeline.py",
      "/opt/astro-project/scripts/run_e2e.sh",
      "/opt/astro-project/tools/post_test_review.py",
      "/opt/astro-project/prefect_grace/flows/**",
      "/opt/astro-project/prefect_grace/tasks/codex_launcher.py",
      "/opt/astro-project/prefect_grace/tasks/telegram_notify.py",
      "/opt/astro-project/prefect_grace/prompts/**",
      "/opt/astro-project/prefect_grace/roles/**",
      "/opt/astro-project/prefect_grace/state/*.yaml",
      "/opt/astro-project/requirements.xml",
      "/opt/astro-project/technology.xml",
      "/opt/astro-project/development-plan.xml",
      "/opt/astro-project/knowledge-graph.xml",
      "/opt/astro-project/verification-matrix.md",
      "/opt/solarsage-astro/**"
    ],
    "must_preserve": [
      "Existing Prefect flows continue to import.",
      "Existing CLI commands keep their current behavior.",
      "Existing tests for `prefect_grace` keep passing unless they encode a bug",
      "No agent execution is started by validation commands.",
      "No real runtime state is written during unit tests.",
      "No secrets are printed in JSON output, logs, or validation errors."
    ],
    "verification": "...",
    "expected_evidence": [
      "`git diff --stat`.",
      "Full list of changed files.",
      "Output of all new unit tests.",
      "Output of nearby regression tests.",
      "Output of compile check.",
      "JSON output of the three CLI smoke checks.",
      "Explicit note that no file outside `Allowed Write Scope` changed."
    ],
    "escalation_triggers": [
      "implementing this packet requires changing Prefect flow execution;",
      "implementing this packet requires changing Codex launcher behavior;",
      "existing historical packets cannot be scanned in warning mode;",
      "strict validation would require rewriting all legacy packets first;",
      "runtime state must be written into source-controlled `prefect_grace/state`;",
      "any product backend/frontend file appears necessary."
    ],
    "source_hash": "60d09569af04a7044ffc1318f191443fa9b0254c61340811e8d9e373e4406d8d",
    "legacy_warnings": []
  },
  "warnings": [],
  "errors": []
}
```

### 8. Allowed Write Scope Adherence Note
No file outside the allowed write scope defined in `Allowed Write Scope` has been created or modified (with the explicit addition of the `grace_lint` verification gate). All changes strictly map to pre-runtime contract layers, test suites, and subcommands.

## Reviewer Notes

Reviewer fills this section.
