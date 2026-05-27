# Execution Packet: FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE-W01-E2E-RUNNER-REGISTRY-SEEDED-SMOKE

## Objective

Add an isolated registry-seeded dry-run smoke for the portable GRACE E2E
packet runner.

The smoke must prove that a temporary runtime registry seeded from bounded
terminal evidence can drive the next runnable packet into the existing dry-run
E2E runner path, while accepted parents are skipped and missing or blocked
dependencies are not executed.

This packet is orchestration-platform work only. It must not change product
Astro behavior and must not start live agents, live Prefect runs, Docker,
backend, frontend, Playwright, provider APIs, or network-dependent services.

## Slice

- slice_id: `SLICE-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`
- slice_slug: `grace-e2e-runner-registry-seeded-smoke`
- feature_id: `FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`
- packet_id: `FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE-W01-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REGISTRY-APPLY-SMOKE-W01-REGISTRY-APPLY-SMOKE, FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP-W01-E2E-STATUS-TRANSITION`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`
- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-REGISTRY-APPLY-SMOKE`
- `M-GRACE-STATUS-MODEL`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions

### 1. Consume Accepted Registry Apply Contract

This packet depends on the registry apply smoke being accepted. It must consume
the accepted bootstrap/registry apply public contract instead of modifying
`prefect_grace/platform/controller_backlog_bootstrap.py`.

If registry apply is not accepted or its apply contract is unstable, this packet
must remain waiting.

### 2. Registry Selects The Runnable Packet

The smoke must not call `run_e2e_packet(...)` on an arbitrary source packet and
call that registry-seeded.

Required flow:

```text
strict synthetic packet corpus
  -> bounded terminal evidence for parent
  -> temp registry apply
  -> sync-packets dry-run/read-only confirmation
  -> submit-packets dry-run registry plan
  -> choose exactly one runnable child packet from registry plan
  -> run dry-run E2E packet runner on that child
  -> record registry transition only in temp state
```

Accepted parents with unchanged source hashes must not be selected for E2E
execution.

### 3. Temp State And Temp Worktrees Only

The smoke must require explicit temporary roots for state, worktrees, and
synthetic packets. It must reject or fail closed for:

```text
/var/lib/grace-orchestrator/**
prefect_grace/state/*.yaml
```

All runtime writes must stay under the explicit temporary roots.

### 4. Source Packets Stay Immutable

The smoke may create synthetic source packets under pytest or CLI temporary
`packet_root`, but it must not mutate real source packets, reviews, summaries,
evidence, or existing packet directories.

The real repository packet corpus may be read for contract context only. It is
not the smoke's write target.

### 5. Dry-Run E2E Runner Only

The E2E runner invocation must use dry-run behavior with deterministic fake
verifier and reviewer outputs.

The smoke must not enable `--execute-agent`, `--no-dry-run`, live Prefect flow
submission, provider credentials, Docker, backend, frontend, or Playwright.

### 6. Preserve Status Separation

The smoke must keep execution domain status, registry status, and planner
selection visible as separate concepts:

- `domain_status` comes from `run_e2e_packet(...)`;
- `registry_status` and `registry_reason` come from the accepted status model;
- `selected_packet_id` comes from registry-aware submission planning.

Only `domain_status=accepted` may be `ok=true`.

### 7. Registry Update Is Bounded And Explicit

After the dry-run E2E runner returns, the smoke may write the selected child
packet's registry transition to the temporary registry for observability.

It must not mark unrelated waiting, blocked, accepted-parent, or missing-dep
packets as accepted. It must not write any registry transition to real
`/var/lib/grace-orchestrator/**` or `prefect_grace/state/*.yaml`.

### 8. Existing CLI JSON Envelope Stays Stable

New or touched CLI commands must keep the established envelope:

```json
{
  "ok": true,
  "project_key": "astro-project",
  "command": "...",
  "result": {},
  "data": {},
  "warnings": [],
  "errors": []
}
```

For commands covered by this packet, `result` must remain equal to `data`.

## Required Implementation Shape

Add a small pure smoke module:

```text
prefect_grace/platform/e2e_runner_registry_seeded_smoke.py
```

Preferred public API:

```python
@dataclass(frozen=True)
class E2ERegistrySeededSmokeCase:
    name: str
    packet_id: str
    expected_status: str
    actual_status: str | None
    selected_for_e2e: bool
    ok: bool
    warnings: list[str]
    errors: list[dict[str, Any]]


@dataclass(frozen=True)
class E2ERegistrySeededSmokeResult:
    ok: bool
    project_key: str
    state_root: str
    worktree_root: str
    packet_root: str
    selected_packet_id: str | None
    bootstrap_apply_count: int
    sync_plan: dict[str, Any]
    submit_plan: dict[str, Any]
    e2e_result: dict[str, Any] | None
    registry_before: dict[str, Any]
    registry_after: dict[str, Any]
    cases: list[E2ERegistrySeededSmokeCase]
    prefect_runs_created: int
    live_agents_started: int
    writes_outside_temp_roots: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]
```

Preferred function:

```python
def run_e2e_runner_registry_seeded_smoke(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    json_safe: bool = True,
) -> E2ERegistrySeededSmokeResult:
    ...
```

The implementation may use a different internal dataclass layout, but the
returned JSON-safe shape must expose equivalent evidence.

## Required CLI

Add a command:

```bash
python3 -m prefect_grace.cli run-e2e-registry-seeded-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-e2e-registry-seeded-smoke/state \
  --worktree-root /tmp/grace-e2e-registry-seeded-smoke/worktrees \
  --packet-root /tmp/grace-e2e-registry-seeded-smoke/packets \
  --json
```

CLI requirements:

- `--project` accepts the existing project config path;
- `--state-root` is required and must reject `/var/lib/grace-orchestrator/**`;
- `--state-root` must reject paths inside `prefect_grace/state`;
- `--worktree-root` is required and must reject the repository root;
- `--packet-root` is required and must be a synthetic temporary packet root;
- `--json` returns the stable envelope with command `run-e2e-registry-seeded-smoke`;
- no flag may start live agents, live Prefect runs, Docker, backend, frontend, or Playwright.

## Required Synthetic Scenario

Build a deterministic packet corpus under the smoke `packet_root`:

- `PARENT-ACCEPTED`: has bounded terminal evidence and is seeded `accepted`;
- `CHILD-RUNNABLE`: depends on `PARENT-ACCEPTED` and becomes ready/runnable;
- `CHILD-MISSING-DEP`: depends on a missing packet and remains waiting;
- `CHILD-BLOCKED-DEP`: depends on a blocked packet and remains waiting or cascading blocked;
- `PARENT-SOURCE-STATUS-ONLY`: has source `status: accepted` but no bounded terminal evidence and must not seed accepted.

The submission plan must select exactly `CHILD-RUNNABLE` for dry-run E2E
execution.

## Required Test Matrix

Use pytest `tmp_path` for all state, packet, evidence, and worktree roots.

Required cases:

- temp apply seeds `PARENT-ACCEPTED` as accepted from bounded terminal evidence;
- accepted parent with unchanged source hash is skipped by E2E selection;
- `CHILD-RUNNABLE` is selected only after its parent is accepted in registry;
- missing dependency keeps `CHILD-MISSING-DEP` waiting and unselected;
- blocked dependency keeps `CHILD-BLOCKED-DEP` waiting or cascading blocked and unselected;
- source `status: accepted` alone does not seed `PARENT-SOURCE-STATUS-ONLY` accepted;
- exactly one dry-run E2E runner invocation occurs;
- E2E runner returns `domain_status=accepted`, `registry_status=accepted`, and `registry_reason=execution_accepted` for the selected child;
- selected child registry transition is written only to temp state;
- no Prefect runs are created;
- no live agent launcher is invoked;
- CLI JSON envelope remains stable for `run-e2e-registry-seeded-smoke`;
- existing `run-e2e-packet --json` and `submit-packets --dry-run --json` contracts remain stable.

## Allowed Write Scope

- `prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`
- `prefect_grace/cli.py`
- `tests/test_prefect_grace_e2e_runner_registry_seeded_smoke.py`
- `tests/test_prefect_grace_cli_e2e_runner_registry_seeded_smoke.py`
- `tests/test_prefect_grace_e2e_packet_runner.py`
- `tests/test_prefect_grace_cli_e2e_packet_runner.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/**`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `prefect_grace/platform/controller_backlog_bootstrap.py`
- `prefect_grace/platform/status_model.py`
- `prefect_grace/platform/backlog_controller.py`
- `prefect_grace/platform/registry_apply_smoke.py`
- `prefect_grace/platform/e2e_packet_runner.py`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/codex_launcher.py`
- `prefect_grace/state/*.yaml`
- `scripts/pipeline.py`
- `scripts/run_e2e.sh`
- `.env`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Existing `validate-project`, `scan-packets`, `sync-packets`, `submit-packets`, `registry-apply-smoke`, `run-e2e-packet`, and `registry-dump` JSON envelopes.
- Existing CLI envelope fields: `ok`, `project_key`, `command`, `result`, `data`, `warnings`, `errors`.
- `result == data` for JSON commands covered by this packet.
- Accepted parent packets with unchanged source hashes are not rerun.
- Missing or blocked dependency packets are not selected for E2E execution.
- Source packet status alone cannot seed accepted registry state.
- `domain_status`, `registry_status`, `registry_reason`, and selected registry plan fields remain distinct in output.
- Dry-run E2E runner behavior remains deterministic and fake-output based.
- `submit-packets --dry-run` never creates Prefect flow runs.
- No live agents, live Prefect runs, provider APIs, Docker, backend, frontend, or Playwright are started.
- Source packets, `prefect_grace/state/*.yaml`, and real `/var/lib/grace-orchestrator/**` are not mutated.
- Product backend/frontend files remain untouched.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_runner_registry_seeded_smoke.py \
  tests/test_prefect_grace_cli_e2e_runner_registry_seeded_smoke.py \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
```

Run targeted GRACE lint for changed platform modules and CLI:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/e2e_runner_registry_seeded_smoke.py \
  prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke for the proposed command:

```bash
python3 -m prefect_grace.cli run-e2e-registry-seeded-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-e2e-registry-seeded-smoke/state \
  --worktree-root /tmp/grace-e2e-registry-seeded-smoke/worktrees \
  --packet-root /tmp/grace-e2e-registry-seeded-smoke/packets \
  --json
```

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, or
live agents for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output for registry-seeded E2E smoke, E2E runner, E2E CLI, and CLI contracts.
- Compile output for `prefect_grace/platform` and `prefect_grace/cli.py`.
- Targeted `scripts/grace_lint.py` output for changed platform modules and CLI.
- `run-e2e-registry-seeded-smoke --json` output showing temp roots, selected packet id, bootstrap apply count, registry-aware `sync_plan`, registry-aware `submit_plan`, E2E result, registry before/after, case verdicts, zero Prefect runs, zero live agents, and no writes outside temp roots.
- Evidence that accepted parent packets with unchanged source hashes are skipped by E2E selection.
- Evidence that only `CHILD-RUNNABLE` is selected and run.
- Evidence that missing or blocked dependency packets remain waiting/cascading and unselected.
- Evidence that source packet status alone does not seed accepted.
- Evidence that selected child registry transition is written only to temp state.
- Confirmation that source packets, `prefect_grace/state/*.yaml`, real `/var/lib/grace-orchestrator/**`, backend, frontend, live agents, live Prefect runs, Docker, and Playwright were not touched.

## Escalation Triggers

- Registry apply smoke is not accepted or its apply contract remains unstable.
- The smoke requires changes to `controller_backlog_bootstrap.py`.
- The smoke requires changing `status_model.py` transition semantics.
- The smoke requires changing `backlog_controller.py` dependency semantics.
- The smoke requires changing `e2e_packet_runner.py` domain status semantics.
- More than one packet is selected for E2E execution.
- The selected packet cannot be derived from registry state.
- The smoke needs to write to real `/var/lib/grace-orchestrator/**`.
- The smoke needs to mutate `prefect_grace/state/*.yaml`.
- The smoke needs to mutate real source packets, reviews, summaries, or evidence.
- Implementation requires live agents, live Prefect runs, provider credentials, Docker, backend, frontend, or Playwright.
- Product backend/frontend files would need changes.

## Reviewer Gate

Reviewer must reject this packet if:

- any write escapes the explicit temporary smoke roots;
- real `/var/lib/grace-orchestrator/**` or `prefect_grace/state/*.yaml` is mutated;
- real source packets are mutated by smoke, sync, bootstrap, submit, or E2E commands;
- `controller_backlog_bootstrap.py` is changed in this packet;
- accepted parents with unchanged source hashes are rerun;
- missing or blocked dependencies are selected for E2E execution;
- source packet status alone can seed accepted;
- more than one packet is run by the smoke;
- `domain_status` and `registry_status` are conflated;
- `submit-packets --dry-run` creates Prefect runs;
- `run_e2e_packet(...)` starts a live agent;
- the JSON envelope changes for existing CLI commands;
- live agents, live Prefect runs, Docker, backend, frontend, or Playwright are started.
