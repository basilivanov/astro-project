# Execution Packet: GRACE Prefect E2E Live Smoke MVP

## Objective

Add the first controlled live smoke path for the portable GRACE packet
orchestrator.

After native submission targets the full E2E runner, the next required proof is
not another offline unit test. The platform needs one operator-safe path that
can prove:

```text
Prefect deployment exists
→ submit-packets submits one ready packet to the E2E deployment
→ Prefect worker picks it up
→ E2E flow returns a domain result
→ registry records submitted run metadata
→ operator can see the run and artifact in Prefect UI
```

This packet adds that live-smoke harness and E2E deployment wiring. It must stay
small, explicit, and reversible. It is not a merge steward, not a batch policy
change, not a feature pipeline refactor, and not a broad live-agent rollout.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP`
- slice_slug: `grace-prefect-e2e-live-smoke-mvp`
- feature_id: `FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP`
- packet_id: `FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP-W01-E2E-LIVE-SMOKE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP-W01-NATIVE-E2E-SUBMISSION`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/deploy_live.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_deploy_live.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`

## Impacted Modules

- `M-GRACE-E2E-PREFECT-FLOW`
- `M-GRACE-PREFECT-DEPLOYMENT`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-LIVE-SMOKE`
- `M-GRACE-CLI`
- `M-GRACE-REGISTRY-STATE`

## Recommended Role Assignment

- context collector: `Haiku` or equivalent cheap model, useful to inspect deployment naming, runtime config, and live smoke conventions.
- coder: `Sonnet high` or `Codex high`; small ops wiring and smoke harness with mocked Prefect in tests.
- verifier: `Codex medium`; must run deployment tests, native submission tests, CLI smoke tests, and optional operator live smoke only when explicitly enabled.
- reviewer: `Codex xhigh` or `Opus`; must verify safety gates, no product changes, no uncontrolled live agent execution, and no feature-pipeline coupling.
- rework policy: fresh context for deployment/submission safety bugs; light resume only for CLI output or artifact wording fixes.

## Required Design Decisions

### 1. Register The E2E Packet Runner Deployment

Extend the live deployment setup so it can register the E2E packet runner
deployment:

```text
prefect-grace-e2e-packet-runner/live-e2e-packet-runner
```

Expected deployment entrypoint:

```text
prefect_grace/flows/e2e_packet_runner_flow.py:e2e_packet_runner_flow
```

Expected queue:

```text
runtime.live_queue_name
```

Expected tags:

- `grace`;
- `packet`;
- `e2e`;
- `live`;

The deployment must use the same work pool, working directory, and Prefect API
configuration conventions as existing deployments.

Do not remove existing deployments. Do not change feature-pipeline deployment
behavior.

### 2. Deployment Creation Must Stay Explicit

This packet may update `prefect_grace/deploy_live.py`, but deployment creation
must remain an explicit operator command.

Allowed:

```bash
python3 -m prefect_grace.deploy_live
```

Forbidden:

- deployment registration as an import side effect;
- deployment registration during unit tests;
- deployment registration from `submit-packets`;
- modifying docker/systemd/nginx configuration.

Tests must stub Prefect deployment APIs and must not call a live Prefect server.

### 3. Add A Controlled Live Smoke Harness

Add an operator smoke command or script that creates/submits exactly one smoke
packet and reports the resulting Prefect run reference.

Preferred CLI command:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-live-smoke \
  --project-config /opt/astro-project/prefect_grace/project.yaml \
  --state-root /tmp/grace-live-smoke-state \
  --worktree-root /tmp/grace-live-smoke-worktrees \
  --packet-root /tmp/grace-live-smoke-packets \
  --dry-run \
  --json
```

Acceptable alternative:

```text
prefect_grace/platform/prefect_e2e_live_smoke.py
```

with a CLI wrapper.

The harness must:

1. create a temporary strict controller packet under the provided packet root;
2. sync/load it into the registry or create the minimum registry record needed by native submission;
3. submit exactly one packet through `submit_ready_packets_to_prefect(..., runner_kind="e2e", limit=1)`;
4. return JSON with `packet_id`, `flow_run_id`, `deployment_name`, `runner_kind`, `idempotency_key`, and `status`;
5. refuse to continue if more than one packet would be submitted.

### 4. Smoke Modes

Support two explicit smoke modes.

#### Mode A — Prefect live, no live agent

Default mode:

```text
dry_run=True
execute_agent=False
```

This creates a real Prefect flow run, but the E2E flow itself uses dry-run
agent behavior and fake verifier/reviewer output if needed. This mode is the
mandatory acceptance path.

#### Mode B — Optional one-packet live agent

Optional mode:

```text
dry_run=False
execute_agent=True
```

This mode must require all of:

- explicit `--execute-agent`;
- explicit `--no-dry-run`;
- explicit `--allow-live-agent-smoke`;
- environment variable `GRACE_ALLOW_LIVE_AGENT_SMOKE=1`;
- `--limit 1` or equivalent hardcoded single-packet guard.

If any guard is missing, fail closed with a structured operator error.

Unit tests must not run Mode B against a real agent.

### 5. Smoke Packet Must Be Low Risk

The generated smoke packet must be intentionally low risk.

Allowed write scope for the smoke packet:

```text
scratch/grace-live-smoke/**
```

Frozen scope must include:

- `backend/**`;
- `frontend/**`;
- `prefect_grace/**` except the smoke packet artifact area;
- `.env`;
- `docker-compose*.yml`;
- `scripts/**`;
- `tools/**`.

The smoke packet objective must be a no-op or scratch-only write. It must not
change product behavior.

### 6. Observe The Prefect Run

The smoke harness must expose enough operator data to find the run in Prefect
UI:

- flow run id;
- flow run name;
- deployment name;
- work queue name;
- runner kind;
- packet id;
- feature id;
- idempotency key;
- URL if available from runtime config.

If Prefect artifact publication is unavailable, the smoke may still pass if the
flow run is submitted and registry metadata is correct.

### 7. Keep Native Submission Semantics

The smoke harness must use existing native submission primitives.

Do not reimplement:

- backlog ordering;
- packet registry storage;
- idempotency keys;
- Prefect client calls;
- deployment name resolution.

If a small helper is missing, add it narrowly with tests.

### 8. No Merge / Acceptance Steward

This packet must not merge, squash, push, accept, or clean up live worktrees
after success.

The smoke may report:

```text
submitted
```

or:

```text
flow_run_created
```

It must not claim the packet is accepted unless the E2E flow result actually
returns `domain_status=accepted`.

### 9. No Feature Pipeline Coupling

The smoke path must not use:

- `prefect_grace/flows/feature_pipeline.py`;
- `prefect-grace-feature-pipeline/live-feature-pipeline`;
- old `feature:*` business feature pipeline runs.

The smoke is for the portable packet orchestrator only.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/deploy_live.py`
- `/opt/astro-project/prefect_grace/platform/prefect_e2e_live_smoke.py`
- `/opt/astro-project/prefect_grace/cli.py`

Narrow integration changes if required:

- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_deploy_live.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_e2e_live_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_live_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/e2e_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing native E2E submission behavior remains unchanged except for smoke usage.
- Existing deployment tests continue to pass with updated E2E deployment expectations.
- Existing `submit-packets` tests continue to pass.
- Existing E2E flow tests continue to pass.
- No product backend/frontend files are modified.
- Unit tests do not call live Prefect, live agents, provider APIs, Docker, backend, or frontend.
- Deployment registration is explicit and never happens on import.
- Live-agent smoke is impossible without all explicit guards.
- Smoke submits at most one packet.
- No merge, push, squash, accept, or delete-worktree behavior is added.
- The feature pipeline deployment remains unchanged.

## Required Implementation Shape

### Deployment Wiring

Add E2E deployment registration to `deploy_live.deploy_flows()`:

```python
"e2e_packet_runner": _apply_deployment(
    entrypoint="prefect_grace/flows/e2e_packet_runner_flow.py:e2e_packet_runner_flow",
    deployment_name="live-e2e-packet-runner",
    ...
)
```

The full deployment name used by submitters must remain:

```text
prefect-grace-e2e-packet-runner/live-e2e-packet-runner
```

### Smoke Result Model

Add a JSON-safe result model similar to:

```python
@dataclass(frozen=True)
class PrefectE2ELiveSmokeResult:
    ok: bool
    mode: str
    packet_id: str
    flow_run_id: str | None
    flow_run_name: str | None
    deployment_name: str
    runner_kind: str
    idempotency_key: str | None
    submitted: bool
    errors: list[dict[str, Any]]
```

### Smoke Function

Add a public function:

```python
def run_prefect_e2e_live_smoke(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    dry_run: bool = True,
    execute_agent: bool = False,
    allow_live_agent_smoke: bool = False,
    limit: int = 1,
    submitter: Callable[..., dict[str, Any]] | None = None,
) -> PrefectE2ELiveSmokeResult:
    ...
```

The function must fail closed for unsafe live-agent combinations.

### CLI

Add:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-live-smoke --help
```

Required flags:

- `--project-config`;
- `--state-root`;
- `--worktree-root`;
- `--packet-root`;
- `--dry-run`;
- `--no-dry-run`;
- `--execute-agent`;
- `--allow-live-agent-smoke`;
- `--json`.

Exit codes:

- `0` if smoke submission is safe and successful;
- `1` if smoke is safely blocked by domain/operator guard;
- `2` for command/runtime errors.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_deploy_live.py \
  tests/test_prefect_grace_prefect_e2e_live_smoke.py \
  tests/test_prefect_grace_cli_prefect_e2e_live_smoke.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run focused regressions:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_e2e_packet_runner_flow.py \
  tests/test_prefect_grace_e2e_packet_runner.py
```

Run static checks:

```bash
python3 -m compileall -q \
  prefect_grace/deploy_live.py \
  prefect_grace/platform/prefect_e2e_live_smoke.py \
  prefect_grace/cli.py

python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_e2e_live_smoke.py

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run offline CLI smoke with a fake submitter/test fixture:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-live-smoke \
  --project-config /tmp/grace-live-smoke/project.yaml \
  --state-root /tmp/grace-live-smoke/state \
  --worktree-root /tmp/grace-live-smoke/worktrees \
  --packet-root /tmp/grace-live-smoke/packets \
  --dry-run \
  --json
```

Optional operator-only live Prefect smoke after review acceptance:

```bash
python3 -m prefect_grace.deploy_live
python3 -m prefect_grace.cli run-prefect-e2e-live-smoke \
  --project-config /opt/astro-project/prefect_grace/project.yaml \
  --state-root /tmp/grace-live-smoke-state \
  --worktree-root /tmp/grace-live-smoke-worktrees \
  --packet-root /tmp/grace-live-smoke-packets \
  --dry-run \
  --json
```

Do not run optional live-agent smoke unless the controller explicitly approves
it after the dry-run Prefect smoke passes.

## Expected Evidence

Attach under `EVIDENCE/attempt-XXXX/`:

- targeted pytest output;
- focused regression pytest output;
- compile output;
- GRACE lint output;
- packet validation JSON;
- deployment test output proving E2E deployment is registered by `deploy_live`;
- offline CLI smoke JSON;
- fake submitter execution evidence showing exactly one packet submitted to E2E deployment;
- `git diff --stat`;
- full changed file list;
- explicit note that unit tests did not call live agents, provider APIs, live Prefect, Docker, product backend/frontend services, merge, squash, or push;
- if optional operator live smoke is run, include Prefect flow run id, URL, deployment name, queue name, and final domain/registry status.

## Escalation Triggers

Stop and ask the controller if:

- implementation needs to modify product backend/frontend code;
- implementation needs to modify `feature_pipeline.py`;
- implementation needs to modify `codex_launcher.py`;
- implementation needs to change E2E runner status semantics;
- implementation requires broad deployment/runtime config redesign;
- live-agent smoke seems necessary before dry-run Prefect smoke passes;
- more than one packet would be submitted by the smoke harness;
- smoke packet needs write scope outside `scratch/grace-live-smoke/**`;
- tests require a live Prefect server.

## Reviewer Checklist

- E2E deployment is added explicitly and safely.
- Existing deployments are preserved.
- Smoke harness submits exactly one packet.
- Smoke harness defaults to Prefect live / agent dry-run mode.
- Live-agent mode is impossible without all explicit guards.
- `submit-packets` and native submission primitives are reused, not forked.
- No feature-pipeline coupling is introduced.
- No product files are touched.
- Unit tests are offline and deterministic.
- Frozen scope is clean.
