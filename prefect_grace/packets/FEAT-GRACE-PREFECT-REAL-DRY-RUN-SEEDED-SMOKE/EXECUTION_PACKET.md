# Execution Packet: FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE-W01-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE

## Objective

Add a registry-seeded real Prefect dry-run smoke for the portable GRACE
orchestrator.

The smoke must prove that a temporary runtime registry seeded from bounded
terminal evidence can drive exactly one runnable scratch packet into the real
Prefect E2E packet runner deployment with `dry_run=true` and
`execute_agent=false`.

This packet is orchestration-platform work only. It must not start live agents,
must not mutate real GRACE runtime state, and must not touch product Astro
backend or frontend behavior.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- slice_slug: `grace-prefect-real-dry-run-seeded-smoke`
- feature_id: `FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- packet_id: `FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE-W01-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE-W01-E2E-RUNNER-REGISTRY-SEEDED-SMOKE, FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP-W01-REAL-E2E-DRY-RUN-SMOKE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/platform/registry_apply_smoke.py`
- `/opt/astro-project/prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`
- `/opt/astro-project/prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- `M-GRACE-REGISTRY-APPLY-SMOKE`
- `M-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-PREFECT-SUBMITTER`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions

### 1. Consume Accepted Seeded Contracts

This packet starts only after the registry apply smoke and registry-seeded E2E
runner smoke are accepted.

It must consume their public contracts. Do not modify
`prefect_grace/platform/controller_backlog_bootstrap.py`,
`prefect_grace/platform/registry_apply_smoke.py`, or
`prefect_grace/platform/e2e_runner_registry_seeded_smoke.py` in this packet.

If those contracts are unstable, this packet must stay waiting.

### 2. Registry Plan Selects The Prefect Submission

The smoke must not submit a manually chosen packet.

Required flow:

```text
synthetic strict packet corpus under packet_root
  -> bounded terminal evidence for accepted parent
  -> temp bootstrap/registry apply
  -> sync-packets dry-run/read-only confirmation
  -> submit-packets dry-run registry plan
  -> choose exactly one runnable child packet from registry plan
  -> submit that child to real Prefect E2E runner with agent dry-run params
```

Accepted parents with unchanged source hashes must not be submitted.
Missing-dependency and blocked-dependency packets must not be submitted.

### 3. Real Prefect Is Allowed, Live Agents Are Not

This packet may create exactly one real Prefect flow run when the real Prefect
server and worker are available.

The submitted E2E flow parameters must include:

- `dry_run=true`;
- `execute_agent=false`;
- `runner_kind=e2e`;
- `limit=1` or equivalent single-packet submission guard.

No flag or code path in this packet may launch Codex, Claude, agy, OpenRouter,
OpenAI, cliproxy, or any other live agent/provider execution.

### 4. Temp Runtime State Only

The smoke must require explicit temporary roots for state, worktrees, and
synthetic packets.

It must reject or fail closed for write targets under:

```text
/var/lib/grace-orchestrator/**
prefect_grace/state/*.yaml
```

All smoke-generated packets, registry files, worktrees, and evidence must stay
under explicit temp roots supplied by tests or CLI.

### 5. Source Packets Are Read-Only Inputs

The real repository packet corpus may be read for contract context only.

The smoke must not mutate real source packets, reviews, summaries, evidence, or
existing packet directories. Synthetic fixtures must live under the supplied
`packet_root`.

### 6. Preserve JSON Envelope And Result Equality

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

### 7. Timeout And Prefect Unavailability Fail Clearly

If Prefect is unavailable, the smoke must return a structured `ok=false` result
or mark real-Prefect verification as not run in evidence. It must not fake a
real Prefect pass.

If waiting for the flow run times out, return `ok=false` with a structured error
such as:

```json
{"code": "PREFECT_SEEDED_DRY_RUN_TIMEOUT", "message": "..."}
```

### 8. Submit Execute Safety Remains Closed

This packet must not weaken `submit-packets --execute` safety gates.

The smoke may submit through a dedicated smoke harness that forces dry-run agent
parameters, but it must not make ordinary execute mode create live-agent runs
without existing explicit safety gates.

### 9. Operator Evidence Must Distinguish Layers

The result must keep these concepts separate:

- registry apply result;
- sync dry-run plan;
- submit dry-run plan;
- selected packet id;
- Prefect submission metadata;
- Prefect state;
- E2E domain status;
- live agent execution count.

`ok=true` requires zero live agents, one selected packet, one submitted Prefect
run, the expected E2E deployment, and successful dry-run state or accepted
dry-run domain status when waiting is enabled.

## Required Implementation Shape

Add a small smoke module:

```text
prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py
```

Preferred public API:

```python
@dataclass(frozen=True)
class PrefectRealDryRunSeededSmokeResult:
    ok: bool
    project_key: str
    mode: str
    state_root: str
    worktree_root: str
    packet_root: str
    selected_packet_id: str | None
    bootstrap_apply_count: int
    sync_plan: dict[str, Any]
    submit_plan: dict[str, Any]
    deployment_name: str | None
    work_queue_name: str | None
    flow_run_id: str | None
    flow_run_name: str | None
    flow_run_url: str | None
    submitted: bool
    waited: bool
    prefect_state_type: str | None
    prefect_state_name: str | None
    domain_status: str | None
    artifact_ids: list[str]
    prefect_runs_created: int
    live_agents_started: int
    writes_outside_temp_roots: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]
```

Preferred function:

```python
def run_prefect_real_dry_run_seeded_smoke(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 5,
    wait: bool = True,
    json_safe: bool = True,
) -> PrefectRealDryRunSeededSmokeResult:
    ...
```

The implementation may use a different internal model, but returned JSON must
expose equivalent evidence.

## Required CLI

Add a command:

```bash
python3 -m prefect_grace.cli run-prefect-real-dry-run-seeded-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-prefect-real-dry-run-seeded-smoke/state \
  --worktree-root /tmp/grace-prefect-real-dry-run-seeded-smoke/worktrees \
  --packet-root /tmp/grace-prefect-real-dry-run-seeded-smoke/packets \
  --timeout-seconds 900 \
  --json
```

CLI requirements:

- `--project` accepts the existing project config path;
- `--state-root`, `--worktree-root`, and `--packet-root` are required;
- `--state-root` must reject `/var/lib/grace-orchestrator/**`;
- `--state-root` must reject paths inside `prefect_grace/state`;
- `--worktree-root` must reject the repository root;
- `--packet-root` must be a synthetic temporary packet root;
- `--no-wait` is allowed and verifies only run creation;
- `--execute-agent` must be rejected fail-closed if exposed by shared parsing;
- `--json` returns the stable envelope with command `run-prefect-real-dry-run-seeded-smoke`;
- no flag may start live agents, Docker, backend, frontend, or Playwright.

## Required Synthetic Scenario

Build a deterministic packet corpus under `packet_root`:

- `PARENT-ACCEPTED`: has bounded terminal evidence and is seeded `accepted`;
- `CHILD-RUNNABLE`: depends on `PARENT-ACCEPTED` and is selected for Prefect dry-run;
- `CHILD-MISSING-DEP`: depends on a missing packet and remains waiting;
- `CHILD-BLOCKED-DEP`: depends on a blocked packet and remains waiting or cascading blocked;
- `PARENT-SOURCE-STATUS-ONLY`: has source `status: accepted` but no bounded terminal evidence and must not seed accepted.

Exactly `CHILD-RUNNABLE` may be submitted to real Prefect.

## Required Test Matrix

Use pytest `tmp_path` for all state, packet, worktree, and evidence roots.

Required cases:

- temp apply seeds only the parent with bounded terminal evidence;
- accepted parent with unchanged source hash is skipped by Prefect submission;
- exactly one child is selected from registry-aware submit planning;
- missing dependency remains waiting and unsubmitted;
- blocked dependency remains waiting or cascading blocked and unsubmitted;
- source packet status alone does not seed accepted;
- command-level `{"status": "passed"}` evidence does not seed accepted;
- no-wait mode succeeds after one mocked real Prefect run is created;
- wait mode succeeds for completed Prefect state with accepted/check-passed dry-run domain status;
- wait mode times out with `PREFECT_SEEDED_DRY_RUN_TIMEOUT`;
- unexpected deployment name fails closed;
- `--execute-agent` is rejected before submission;
- no live agent launcher is invoked;
- no writes escape temp roots;
- CLI JSON envelope remains stable for `run-prefect-real-dry-run-seeded-smoke`, `sync-packets`, and `submit-packets`.

## Allowed Write Scope

- `prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py`
- `prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py`
- `prefect_grace/cli.py`
- `tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py`
- `tests/test_prefect_grace_cli_prefect_real_dry_run_seeded_smoke.py`
- `tests/test_prefect_grace_prefect_e2e_real_dry_run_smoke.py`
- `tests/test_prefect_grace_prefect_native_submission.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE/**`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `prefect_grace/platform/controller_backlog_bootstrap.py`
- `prefect_grace/platform/registry_apply_smoke.py`
- `prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`
- `prefect_grace/platform/prefect_native_submission.py`
- `prefect_grace/platform/runtime_adapter.py`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/codex_launcher.py`
- `prefect_grace/state/*.yaml`
- `scripts/pipeline.py`
- `scripts/run_e2e.sh`
- `docker-compose*.yml`
- `.env`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Existing `validate-project`, `scan-packets`, `sync-packets`, `submit-packets`, `registry-apply-smoke`, `run-e2e-registry-seeded-smoke`, `run-prefect-e2e-real-dry-run-smoke`, and `registry-dump` JSON envelopes.
- Existing CLI envelope fields: `ok`, `project_key`, `command`, `result`, `data`, `warnings`, `errors`.
- `result == data` for JSON commands covered by this packet.
- Accepted parent packets with unchanged source hashes are not submitted.
- Missing or blocked dependency packets are not submitted.
- Source packet status alone cannot seed accepted registry state.
- `submit-packets --dry-run` never creates Prefect flow runs.
- The smoke creates at most one real Prefect flow run.
- The submitted flow uses `dry_run=true` and `execute_agent=false`.
- No live agents, provider APIs, Docker, backend, frontend, or Playwright are started by tests or default CLI smoke.
- Source packets, `prefect_grace/state/*.yaml`, and real `/var/lib/grace-orchestrator/**` are not mutated.
- Product backend/frontend files remain untouched.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py \
  tests/test_prefect_grace_cli_prefect_real_dry_run_seeded_smoke.py \
  tests/test_prefect_grace_prefect_e2e_real_dry_run_smoke.py \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
```

Run targeted GRACE lint for changed platform modules and CLI:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py \
  prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py \
  prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI guard smoke with mocked/unit path if implemented:

```bash
python3 -m prefect_grace.cli run-prefect-real-dry-run-seeded-smoke \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-prefect-real-dry-run-seeded-smoke/state \
  --worktree-root /tmp/grace-prefect-real-dry-run-seeded-smoke/worktrees \
  --packet-root /tmp/grace-prefect-real-dry-run-seeded-smoke/packets \
  --no-wait \
  --json
```

If the real Prefect server and worker are unavailable, do not fake the real
Prefect verification. Record `not_run_prefect_unavailable` in evidence.

Do not run Docker, backend, frontend, Playwright, live agents, or provider APIs
for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output for `prefect_grace/platform` and `prefect_grace/cli.py`.
- Targeted `scripts/grace_lint.py` output for changed platform modules and CLI.
- CLI smoke or unit-injected smoke output showing temp roots, selected packet id, bootstrap apply count, sync plan, submit plan, one Prefect run metadata, zero live agents, and no writes outside temp roots.
- Evidence that accepted parents are skipped and only the runnable child is submitted.
- Evidence that missing or blocked dependency packets remain unsubmitted.
- Evidence that source status alone and command-level `status: passed` do not seed accepted.
- Explicit note whether real Prefect was run or not run because unavailable.
- Confirmation that source packets, `prefect_grace/state/*.yaml`, real `/var/lib/grace-orchestrator/**`, backend, frontend, live agents, Docker, and Playwright were not touched.

## Escalation Triggers

- Registry-seeded E2E smoke is not accepted or its contract remains unstable.
- The smoke requires changes to `controller_backlog_bootstrap.py`, `registry_apply_smoke.py`, or `e2e_runner_registry_seeded_smoke.py`.
- The smoke requires changing native submission semantics instead of consuming them.
- More than one packet would be submitted.
- The selected packet cannot be derived from registry state.
- The smoke needs to write to real `/var/lib/grace-orchestrator/**`.
- The smoke needs to mutate `prefect_grace/state/*.yaml`.
- The smoke needs to mutate real source packets, reviews, summaries, or evidence.
- Implementation requires live agents, provider credentials, Docker, backend, frontend, or Playwright.
- Product backend/frontend files would need changes.

## Reviewer Gate

Reviewer must reject this packet if:

- any write escapes explicit temporary smoke roots;
- real `/var/lib/grace-orchestrator/**` or `prefect_grace/state/*.yaml` is mutated;
- real source packets are mutated by smoke, sync, bootstrap, or submit commands;
- accepted parents with unchanged source hashes are submitted;
- missing or blocked dependencies are submitted;
- source packet status alone can seed accepted;
- command-level `status: passed` can seed accepted;
- more than one Prefect flow run is created;
- the submitted flow has `execute_agent=true`;
- a live agent launcher is invoked;
- `submit-packets --dry-run` creates Prefect runs;
- the JSON envelope changes for existing CLI commands;
- Docker, backend, frontend, or Playwright are started.
