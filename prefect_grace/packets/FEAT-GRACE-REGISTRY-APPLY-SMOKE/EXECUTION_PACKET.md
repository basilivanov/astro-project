# Execution Packet: FEAT-GRACE-REGISTRY-APPLY-SMOKE-W01-REGISTRY-APPLY-SMOKE

## Objective

Add an isolated, deterministic registry apply smoke for the portable GRACE
orchestrator after the bootstrap backlog rework is accepted.

The smoke must prove that `bootstrap-backlog --apply` can seed a temporary
runtime registry and that follow-up `sync-packets` and `submit-packets` planning
uses that registry correctly, without live agents, Prefect live runs, Docker,
product services, or writes to the real runtime state.

This packet is orchestration-platform work only. It must not touch product Astro
features.

## Slice

- slice_id: `SLICE-GRACE-REGISTRY-APPLY-SMOKE`
- slice_slug: `grace-registry-apply-smoke`
- feature_id: `FEAT-GRACE-REGISTRY-APPLY-SMOKE`
- packet_id: `FEAT-GRACE-REGISTRY-APPLY-SMOKE-W01-REGISTRY-APPLY-SMOKE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP-W01-BACKLOG-BOOTSTRAP`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP/REVIEWS/review-0001.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-REGISTRY-APPLY-SMOKE`
- `M-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-STRICT-PACKET-DISCOVERY`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions

### 1. This Packet Starts After Bootstrap Rework

Do not modify `prefect_grace/platform/controller_backlog_bootstrap.py` in this
packet.

The only allowed dependency on bootstrap behavior is through its accepted public
CLI/module contract after
`FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP-W01-BACKLOG-BOOTSTRAP` is accepted.
If bootstrap remains in rework or its apply contract is unstable, this packet
must stay waiting.

### 2. Temp Runtime State Only

The smoke must use an explicit temporary runtime state root supplied by tests or
CLI. It must never default to or write under:

```text
/var/lib/grace-orchestrator/**
prefect_grace/state/*.yaml
```

Apply mode is allowed only against this temporary state root. Tests must assert
that no write target escapes it.

### 3. Source Packets Are Read-Only Inputs

The smoke may scan strict source packets and bounded packet artifacts, but it
must not mutate source packet markdown, reviews, summaries, evidence, or packet
directories.

Synthetic fixtures for unit tests may be created under pytest `tmp_path`; the
real source packet corpus must remain unchanged.

### 4. Terminal Evidence Must Be Bounded

Source packet status alone is not enough to seed `accepted`.

Accepted or blocked runtime state may be seeded only from bounded terminal
evidence produced by the accepted bootstrap contract, such as accepted review
artifacts, packet-level summary status, or schema-owned evidence manifest
fields. Generic command-level `status: passed` or source `status: accepted`
must not infer registry `accepted`.

### 5. Registry State Drives Planning

After temporary apply, the smoke must prove that planner behavior comes from the
runtime registry state, not from source markdown status alone:

- an accepted parent packet with the same source hash is not submitted or rerun;
- a dependent packet whose dependencies are accepted becomes ready/runnable;
- a dependent packet with a missing dependency stays waiting;
- a dependent packet with a blocked dependency stays waiting or cascading
  blocked, not accepted;
- `sync-packets --dry-run` reports the expected registry-aware plan without
  writing state;
- `submit-packets --dry-run` uses registry state and creates no Prefect runs.

### 6. Submit Execute Remains Fail-Closed

This packet must not weaken existing `submit-packets --execute` safety behavior.

If execute mode is not already explicitly allowed by existing safety gates, it
must fail closed. This smoke must not introduce a shortcut that creates Prefect
runs, starts agents, or marks packets terminal.

### 7. Existing CLI JSON Envelope Stays Stable

New or touched CLI commands must keep the established JSON envelope:

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

For all commands covered by this packet, `result` must remain equal to `data`.

### 8. Offline And Deterministic

The smoke must be fully offline and deterministic. It must not start or require
live agents, Prefect server/worker live runs, Docker, backend, frontend,
Playwright, provider APIs, network calls, or credentials.

## Required Implementation Shape

Add a small pure platform module:

```text
prefect_grace/platform/registry_apply_smoke.py
```

Preferred public API:

```python
@dataclass(frozen=True)
class RegistryApplySmokeCase:
    name: str
    packet_id: str
    expected_status: str
    actual_status: str | None
    expected_action: str
    actual_action: str | None
    ok: bool
    evidence_paths: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]


@dataclass(frozen=True)
class RegistryApplySmokeResult:
    ok: bool
    project_key: str
    state_root: str
    packet_root: str
    dry_run: bool
    bootstrap_apply_count: int
    sync_plan: dict[str, Any]
    submit_plan: dict[str, Any]
    cases: list[RegistryApplySmokeCase]
    prefect_runs_created: int
    writes_outside_state_root: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]
```

Preferred function:

```python
def run_registry_apply_smoke(
    *,
    project_config: Path,
    state_root: Path,
    packet_root: Path | None = None,
    json_safe: bool = True,
) -> RegistryApplySmokeResult:
    ...
```

The implementation may use a different internal model, but it must expose a
JSON-safe result with equivalent fields and enough detail for operator review.

## Required CLI

Add a command shaped like:

```bash
python3 -m prefect_grace.cli registry-apply-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-registry-apply-smoke/state \
  --json
```

CLI requirements:

- `--project` accepts the existing project config path;
- `--state-root` is required and must reject `/var/lib/grace-orchestrator/**`;
- `--state-root` must reject paths inside `prefect_grace/state`;
- `--packet-root` may be optional for synthetic fixture mode, but real source
  packet inputs must remain read-only;
- `--json` returns the stable envelope with command `registry-apply-smoke`;
- no flag may start live agents, live Prefect runs, Docker, backend, frontend,
  or Playwright.

## Required Test Matrix

Use isolated pytest fixtures under `tmp_path` for the decisive registry states.

Required cases:

- accepted parent with same source hash plus bounded terminal evidence is seeded
  accepted in temp registry;
- accepted parent with same source hash is skipped by `submit-packets --dry-run`;
- dependent packet with all dependencies accepted is ready/runnable;
- dependent packet with missing dependency remains waiting, not accepted;
- dependent packet with blocked dependency remains waiting or cascading blocked,
  not accepted;
- source packet `status: accepted` without bounded terminal evidence does not
  seed registry accepted;
- generic command-level evidence such as `{"status": "passed"}` does not seed
  registry accepted;
- `sync-packets --dry-run` after temp apply does not write additional registry
  state;
- `submit-packets --dry-run` creates no Prefect runs and returns registry-based
  planning data;
- `submit-packets --execute` remains fail-closed unless existing safety gates
  explicitly allow execution;
- CLI JSON envelope remains stable for `registry-apply-smoke`, `sync-packets`,
  and `submit-packets`.

## Allowed Write Scope

- `prefect_grace/platform/registry_apply_smoke.py`
- `prefect_grace/cli.py`
- `tests/test_prefect_grace_registry_apply_smoke.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `tests/test_prefect_grace_backlog_controller.py`
- `prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE/**`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `prefect_grace/platform/controller_backlog_bootstrap.py`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/codex_launcher.py`
- `prefect_grace/state/*.yaml`
- `scripts/pipeline.py`
- `scripts/run_e2e.sh`
- `.env`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Existing `validate-project`, `scan-packets`, `sync-packets`, `submit-packets`, `bootstrap-backlog`, and `registry-dump` JSON envelopes.
- Existing CLI envelope fields: `ok`, `project_key`, `command`, `result`, `data`, `warnings`, `errors`.
- `result == data` for JSON commands covered by this packet.
- Source packets are immutable during smoke execution.
- `prefect_grace/state/*.yaml` is not read as the smoke write target and is not mutated.
- Real `/var/lib/grace-orchestrator/**` is not read as the smoke write target and is not mutated.
- Apply writes happen only under the explicit temporary `--state-root`.
- Accepted registry state is seeded only from bounded terminal evidence.
- Accepted parent packets with unchanged source hashes are not submitted again.
- Missing or blocked dependencies do not become accepted by cascade.
- `submit-packets --dry-run` never creates Prefect flow runs.
- `submit-packets --execute` remains fail-closed unless existing safety gates already permit it.
- No live agents, live Prefect runs, provider APIs, Docker, backend, frontend, or Playwright are started.
- Product backend/frontend files remain untouched.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_registry_apply_smoke.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
```

Run targeted GRACE lint for changed platform modules and CLI:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/registry_apply_smoke.py \
  prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke for the proposed command:

```bash
python3 -m prefect_grace.cli registry-apply-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-registry-apply-smoke/state \
  --json
```

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, or
live agents for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output for registry apply smoke, backlog controller, and CLI contracts.
- Compile output for `prefect_grace/platform` and `prefect_grace/cli.py`.
- Targeted `scripts/grace_lint.py` output for changed platform modules and CLI.
- `registry-apply-smoke --json` output showing temp `state_root`, bootstrap apply count, registry-aware `sync_plan`, registry-aware `submit_plan`, case verdicts, zero Prefect runs created, and no writes outside temp state root.
- Evidence that accepted parent packets with unchanged source hashes are skipped by submit planning.
- Evidence that ready dependents become runnable only after accepted deps are in registry state.
- Evidence that missing or blocked dependencies remain waiting/cascading and are not accepted.
- Evidence that source packet status alone and generic command-level `status: passed` evidence do not seed accepted.
- Confirmation that source packets, `prefect_grace/state/*.yaml`, real `/var/lib/grace-orchestrator/**`, backend, frontend, live agents, live Prefect runs, Docker, and Playwright were not touched.

## Escalation Triggers

- Bootstrap rework is not accepted or its apply contract remains unstable.
- The smoke requires changes to `controller_backlog_bootstrap.py`.
- The smoke needs to write to real `/var/lib/grace-orchestrator/**`.
- The smoke needs to mutate `prefect_grace/state/*.yaml`.
- The smoke needs to mutate source packets, reviews, summaries, or evidence.
- Registry planning cannot distinguish accepted deps from source packet status without bounded terminal evidence.
- `submit-packets --dry-run` cannot use registry state without creating Prefect runs.
- `submit-packets --execute` must be opened beyond existing safety gates.
- Implementation requires live agents, live Prefect runs, provider credentials, Docker, backend, frontend, or Playwright.
- Product backend/frontend files would need changes.

## Reviewer Gate

Reviewer must reject this packet if:

- any write escapes the explicit temporary smoke `state_root`;
- real `/var/lib/grace-orchestrator/**` or `prefect_grace/state/*.yaml` is
  mutated;
- source packets are mutated by smoke, sync, bootstrap, or submit commands;
- `controller_backlog_bootstrap.py` is changed in this packet;
- source packet status alone can seed accepted;
- generic command-level `status: passed` can seed accepted;
- accepted parent packets with unchanged source hashes are submitted again;
- missing or blocked dependencies become accepted;
- `submit-packets --dry-run` creates Prefect runs;
- `submit-packets --execute` no longer fails closed under existing safety gates;
- the JSON envelope changes for existing CLI commands;
- live agents, live Prefect runs, Docker, backend, frontend, or Playwright are
  started.
