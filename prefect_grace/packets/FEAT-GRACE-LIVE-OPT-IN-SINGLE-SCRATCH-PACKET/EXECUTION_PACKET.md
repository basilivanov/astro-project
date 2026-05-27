# Execution Packet: FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET-W01-LIVE-OPT-IN-SINGLE-SCRATCH

## Objective

Add the first explicitly opt-in live-agent smoke for the portable GRACE
orchestrator, limited to one synthetic scratch packet.

The smoke must prove that, after the registry-seeded real Prefect dry-run smoke
is accepted, an operator can deliberately run exactly one live-agent E2E packet
against a scratch-only write scope while all product code, real runtime state,
and source packets remain protected.

This packet is orchestration-platform work only. It must not change product
Astro behavior and must not make live-agent execution the default anywhere.

## Slice

- slice_id: `SLICE-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET`
- slice_slug: `grace-live-opt-in-single-scratch-packet`
- feature_id: `FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET`
- packet_id: `FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET-W01-LIVE-OPT-IN-SINGLE-SCRATCH`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE-W01-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET`
- `M-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions

### 1. Live Agent Is Multi-Factor Opt-In Only

Live-agent execution must remain impossible by default.

The live smoke may run only when all required operator gates are present:

- explicit CLI flag such as `--execute-agent`;
- explicit acknowledgement flag such as `--i-understand-live-agent`;
- explicit opt-in token or environment variable such as
  `GRACE_LIVE_AGENT_OPT_IN=single-scratch`;
- explicit temporary `--state-root`, `--worktree-root`, and `--packet-root`;
- one selected synthetic scratch packet from registry-aware planning.

Missing any gate must return `ok=false` before submission or agent launch.

### 2. One Synthetic Scratch Packet Only

The smoke must build one strict synthetic packet under `packet_root`.

The generated packet's allowed write scope must be only:

```text
scratch/grace-live-opt-in-single-scratch/**
```

Its frozen scope must include at minimum:

```text
backend/**
frontend/**
prefect_grace/**
scripts/**
tools/**
docker-compose*.yml
.env
```

The smoke must refuse to run if more than one packet is ready, if the selected
packet is not the synthetic scratch packet, or if any source packet comes from
the real packet corpus.

### 3. Registry State Selects The Packet

The smoke must use the same registry-aware selection path proven by the seeded
dry-run packets.

Required flow:

```text
synthetic scratch packet under packet_root
  -> temp registry seed/sync
  -> submit-packets dry-run registry plan
  -> assert exactly one selected scratch packet
  -> submit/run E2E with dry_run=false and execute_agent=true only after opt-in gates
```

The smoke must not call the agent runner directly on an arbitrary packet.

### 4. Temp Runtime State And Worktree Isolation

The smoke must reject or fail closed for write targets under:

```text
/var/lib/grace-orchestrator/**
prefect_grace/state/*.yaml
```

All registry state, packets, worktrees, and evidence must stay under explicit
temporary roots supplied by tests or CLI.

The live worktree must be preserved for operator inspection by default unless a
separate accepted cleanup contract exists.

### 5. No Product Code Mutation

The live agent may only write inside the scratch path in the isolated worktree.

The smoke must fail if scope evidence shows changes under product backend,
frontend, platform code, scripts, config, source packets, `.env`, Docker files,
or any other frozen path.

No merge, push, squash, commit to main branch, deployment mutation, package
install, Docker start, backend start, frontend start, or Playwright run is
allowed in this packet.

### 6. Prefect Is The Execution Adapter

The preferred live smoke submits one E2E Prefect flow run with:

- `dry_run=false`;
- `execute_agent=true`;
- `runner_kind=e2e`;
- `limit=1`;
- a synthetic scratch packet id;
- the explicit temporary roots.

If implementation chooses a local E2E runner path for test hooks, the real live
path must still be Prefect-visible and operator-auditable.

### 7. Result Must Preserve Status Separation

The JSON result must keep these concepts separate:

- opt-in gate status;
- selected packet id;
- registry status before and after;
- Prefect run metadata;
- agent launch count;
- domain status from E2E runner;
- scope verdict;
- changed files;
- writes outside temp roots.

`ok=true` requires exactly one live agent launch, one selected scratch packet,
scope pass, no writes outside temp roots, and a successful or accepted E2E
domain status.

### 8. Existing Safe Defaults Must Not Move

This packet must not change safe defaults for:

- `submit-packets`;
- `run-e2e-packet`;
- registry apply smoke;
- real Prefect dry-run smoke;
- any batch command.

All existing commands must remain dry-run or fail-closed unless the user opts in
through their already accepted gates.

### 9. Secrets Stay Out Of Evidence

The smoke may require live-agent credentials in the operator environment, but it
must not print raw env values, API keys, tokens, prompts containing secrets, or
provider credentials in JSON output, logs, packet artifacts, or evidence.

## Required Implementation Shape

Add a small live smoke module:

```text
prefect_grace/platform/live_opt_in_single_scratch_packet.py
```

Preferred public API:

```python
@dataclass(frozen=True)
class LiveOptInSingleScratchResult:
    ok: bool
    project_key: str
    mode: str
    opt_in_confirmed: bool
    state_root: str
    worktree_root: str
    packet_root: str
    selected_packet_id: str | None
    registry_before: dict[str, Any]
    registry_after: dict[str, Any]
    submit_plan: dict[str, Any]
    deployment_name: str | None
    work_queue_name: str | None
    flow_run_id: str | None
    flow_run_name: str | None
    flow_run_url: str | None
    agent_launch_count: int
    domain_status: str | None
    scope_verdict: str | None
    changed_files: list[str]
    writes_outside_temp_roots: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]
```

Preferred function:

```python
def run_live_opt_in_single_scratch_packet(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    execute_agent: bool = False,
    acknowledge_live_agent: bool = False,
    opt_in_token: str | None = None,
    timeout_seconds: int = 1800,
    json_safe: bool = True,
) -> LiveOptInSingleScratchResult:
    ...
```

The implementation may use a different internal model, but returned JSON must
expose equivalent gate, selection, execution, and scope evidence.

## Required CLI

Add a command:

```bash
GRACE_LIVE_AGENT_OPT_IN=single-scratch \
python3 -m prefect_grace.cli run-live-opt-in-single-scratch-packet \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-live-opt-in-single-scratch/state \
  --worktree-root /tmp/grace-live-opt-in-single-scratch/worktrees \
  --packet-root /tmp/grace-live-opt-in-single-scratch/packets \
  --execute-agent \
  --i-understand-live-agent \
  --timeout-seconds 1800 \
  --json
```

CLI requirements:

- `--project` accepts the existing project config path;
- `--state-root`, `--worktree-root`, and `--packet-root` are required;
- `--state-root` must reject `/var/lib/grace-orchestrator/**`;
- `--state-root` must reject paths inside `prefect_grace/state`;
- `--worktree-root` must reject the repository root;
- `--packet-root` must be a synthetic temporary packet root;
- `--execute-agent` is required for live execution;
- `--i-understand-live-agent` is required for live execution;
- `GRACE_LIVE_AGENT_OPT_IN=single-scratch` or an equivalent explicit token is required;
- `--json` returns the stable envelope with command `run-live-opt-in-single-scratch-packet`;
- omitting any opt-in gate must fail before Prefect submission or agent launch.

## Required Synthetic Scenario

The generated packet must be deterministic and scratch-only:

- packet id: `LIVE-OPT-IN-SINGLE-SCRATCH-W01-SCRATCH`;
- status: `ready`;
- no dependencies;
- allowed write scope: `scratch/grace-live-opt-in-single-scratch/**`;
- frozen scope: all product, platform, scripts, source packets, config, Docker,
  and secret-bearing paths;
- objective: write a tiny deterministic scratch evidence file only.

No real project source packet may be selected or run.

## Required Test Matrix

Use pytest `tmp_path` for all state, packet, worktree, and evidence roots.

Required cases:

- command without opt-in token fails before submission;
- command without acknowledgement flag fails before submission;
- command without `--execute-agent` fails before submission;
- unsafe `state_root` under `/var/lib/grace-orchestrator/**` is rejected;
- unsafe `state_root` under `prefect_grace/state` is rejected;
- repo-root `worktree_root` is rejected;
- synthetic packet has scratch-only allowed write scope and broad frozen scope;
- registry-aware plan selects exactly the synthetic scratch packet;
- extra ready packet causes fail-closed packet-count error;
- mocked live run records exactly one agent launch;
- mocked scope pass returns `ok=true`;
- mocked scope failure returns `ok=false`;
- no writes escape temp roots;
- existing dry-run commands remain dry-run and JSON envelopes remain stable;
- no secrets or raw env values appear in JSON output.

Real live-agent execution must not run in automated unit tests.

## Allowed Write Scope

- `prefect_grace/platform/live_opt_in_single_scratch_packet.py`
- `prefect_grace/cli.py`
- `tests/test_prefect_grace_live_opt_in_single_scratch_packet.py`
- `tests/test_prefect_grace_cli_live_opt_in_single_scratch_packet.py`
- `tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py`
- `tests/test_prefect_grace_e2e_packet_runner.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `prefect_grace/packets/FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET/**`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `prefect_grace/platform/controller_backlog_bootstrap.py`
- `prefect_grace/platform/registry_apply_smoke.py`
- `prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`
- `prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py`
- `prefect_grace/platform/prefect_native_submission.py`
- `prefect_grace/platform/runtime_adapter.py`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/codex_launcher.py`
- `prefect_grace/prompts/**`
- `prefect_grace/roles/**`
- `prefect_grace/state/*.yaml`
- `scripts/pipeline.py`
- `scripts/run_e2e.sh`
- `docker-compose*.yml`
- `.env`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Existing `validate-project`, `scan-packets`, `sync-packets`, `submit-packets`, `registry-apply-smoke`, `run-e2e-registry-seeded-smoke`, `run-prefect-real-dry-run-seeded-smoke`, and `registry-dump` JSON envelopes.
- Existing CLI envelope fields: `ok`, `project_key`, `command`, `result`, `data`, `warnings`, `errors`.
- `result == data` for JSON commands covered by this packet.
- Live-agent execution is never default behavior.
- Ordinary `submit-packets --dry-run` never creates Prefect runs.
- Ordinary dry-run smokes still use `execute_agent=false`.
- The live smoke can run at most one synthetic scratch packet.
- No real source packet can be selected for live execution.
- Source packets, `prefect_grace/state/*.yaml`, and real `/var/lib/grace-orchestrator/**` are not mutated.
- Product backend/frontend files remain untouched.
- No Docker, backend, frontend, or Playwright processes are started.
- No secrets or raw environment values are printed.

## Verification

Run targeted offline tests:

```bash
pytest -q \
  tests/test_prefect_grace_live_opt_in_single_scratch_packet.py \
  tests/test_prefect_grace_cli_live_opt_in_single_scratch_packet.py \
  tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
```

Run targeted GRACE lint for changed platform modules and CLI:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/live_opt_in_single_scratch_packet.py \
  prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI guard smoke without opt-in and expect fail-closed:

```bash
python3 -m prefect_grace.cli run-live-opt-in-single-scratch-packet \
  --project prefect_grace/project.yaml \
  --state-root /tmp/grace-live-opt-in-single-scratch/state \
  --worktree-root /tmp/grace-live-opt-in-single-scratch/worktrees \
  --packet-root /tmp/grace-live-opt-in-single-scratch/packets \
  --json
```

Real live-agent execution is manual and requires Architect approval plus all
opt-in gates. If it is not run, record `not_run_live_agent_not_approved` in
evidence. Do not run Docker, backend, frontend, or Playwright for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted offline pytest output.
- Compile output for `prefect_grace/platform` and `prefect_grace/cli.py`.
- Targeted `scripts/grace_lint.py` output for changed platform modules and CLI.
- CLI guard smoke output proving missing opt-in fails before submission.
- Unit evidence that synthetic packet write scope is scratch-only and frozen scope is broad.
- Unit evidence that exactly one scratch packet can be selected and mocked live-run path records one agent launch.
- Unit evidence that scope pass/fail controls `ok`.
- Explicit note whether real live-agent smoke was run or not run.
- Confirmation that source packets, `prefect_grace/state/*.yaml`, real `/var/lib/grace-orchestrator/**`, backend, frontend, Docker, and Playwright were not touched.

## Escalation Triggers

- Seeded real Prefect dry-run smoke is not accepted or its contract remains unstable.
- The live smoke requires changing safe defaults on existing commands.
- The live smoke requires selecting a real source packet.
- More than one packet would be submitted or run.
- The live smoke needs to write outside `scratch/grace-live-opt-in-single-scratch/**`.
- The live smoke needs to mutate real `/var/lib/grace-orchestrator/**`.
- The live smoke needs to mutate `prefect_grace/state/*.yaml`.
- The live smoke needs product backend/frontend changes.
- Implementation requires Docker, backend, frontend, Playwright, deployment mutation, merge, push, or commit.
- The live smoke cannot prevent secrets from entering output or evidence.

## Reviewer Gate

Reviewer must reject this packet if:

- any live-agent path is available without all opt-in gates;
- any existing command default starts live agents;
- more than one packet can be run;
- a real source packet can be selected for live execution;
- generated packet scope is not scratch-only;
- scope failure can still return `ok=true`;
- any write escapes explicit temporary roots or scratch scope;
- real `/var/lib/grace-orchestrator/**` or `prefect_grace/state/*.yaml` is mutated;
- product backend/frontend, scripts, config, source packets, Docker files, or `.env` are changed by the live agent;
- Docker, backend, frontend, or Playwright are started;
- raw secrets or env values are printed;
- the JSON envelope changes for existing CLI commands.
