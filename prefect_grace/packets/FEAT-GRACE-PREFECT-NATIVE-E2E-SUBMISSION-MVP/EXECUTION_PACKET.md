# Execution Packet: GRACE Prefect Native E2E Submission MVP

## Objective

Switch native packet submission from the lower-level managed packet runner flow
to the full E2E packet runner flow.

The platform now has an accepted single-packet E2E path:

```text
packet registry readiness
→ isolated worktree
→ managed coder runner
→ scope lifecycle
→ verifier/reviewer handoff
→ domain status
→ registry transition fields
→ Prefect-visible E2E flow wrapper
```

But `submit-packets` still submits the older managed-packet runner seam. This
packet makes the native submission path submit the accepted
`prefect-grace-e2e-packet-runner` flow so a queued packet is visible in Prefect
as a full GRACE lifecycle unit, not just a coder execution shell.

This packet must not implement batch policy changes, merge stewardship,
deployment registration, live-agent defaults, or legacy feature-pipeline
behavior. It is a submission-target switch with tests and rollback-compatible
metadata.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP`
- slice_slug: `grace-prefect-native-e2e-submission-mvp`
- feature_id: `FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP`
- packet_id: `FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP-W01-NATIVE-E2E-SUBMISSION`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP-W01-PREFECT-NATIVE-SUBMISSION, FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW, FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP-W01-E2E-STATUS-TRANSITION`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_runtime_adapter_submit_packet_run.py`

## Impacted Modules

- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-E2E-PREFECT-FLOW`
- `M-GRACE-PREFECT-SUBMITTER`
- `M-GRACE-RUNTIME-ADAPTER`
- `M-GRACE-REGISTRY-STATE`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or equivalent cheap model, useful to map current `submit-packets`, submitter, runtime adapter, and registry record shape.
- coder: `Sonnet high` or `Codex high`; deterministic submission wiring with mocked Prefect submitter, no live server required.
- verifier: `Codex medium`; must run native submission tests, CLI tests, runtime adapter tests, and E2E flow regressions.
- reviewer: `Codex xhigh` or `Opus`; must verify no deployment registration, no local queue, no feature pipeline, and no live defaults slipped in.
- rework policy: fresh context for submission/idempotency/registry semantics changes; light resume only for output wording or test fixture fixes.

## Required Design Decisions

### 1. E2E Flow Becomes The Native Submission Target

Update native submission so the default submitted deployment is the E2E flow:

```text
prefect-grace-e2e-packet-runner/live-e2e-packet-runner
```

The submitted flow parameters must target `e2e_packet_runner_flow(...)`, not
`managed_packet_runner_flow(...)`.

Required parameter mapping:

- `project_root` from `project.repo_root`;
- `packet_path` from parsed/registry packet file path;
- `state_root` from `project.runtime_state_root`;
- `worktree_root` from explicit argument or deterministic default under runtime state;
- `project_key` from `project.project_key`;
- `packet_id`, `attempt`, `base_ref`, `dry_run`, `execute_agent`, `timeout_seconds`, `keep_worktree`.

Do not submit the legacy feature pipeline deployment from this path.

### 2. Keep Managed Submission Available As Rollback Metadata

The packet may preserve the old managed runner submission helpers for backward
compatibility, but the native/default `submit-packets` path must use E2E.

Acceptable implementation options:

- add `runner_kind: Literal["e2e", "managed"] = "e2e"` to the native submission API;
- or add a separate `submit_ready_packets_to_e2e_prefect(...)` and make the CLI call it.

If `runner_kind` is introduced, default must be `e2e`. The managed path may be
kept only as an explicit compatibility path and must remain covered by tests.

### 3. Add E2E Packet Prefect Submitter Helpers

Extend `prefect_grace/tasks/prefect_submitter.py` with E2E packet submission
helpers.

Required constants/functions:

```python
E2E_PACKET_DEPLOYMENT_NAME = "prefect-grace-e2e-packet-runner/live-e2e-packet-runner"

def e2e_packet_flow_run_name(packet_id: str, attempt: int, title: str | None = None) -> str:
    ...

def e2e_packet_flow_parameters(...) -> dict[str, Any]:
    ...

def submit_e2e_packet_flow_run(
    *,
    parameters: dict[str, Any],
    scheduled_for: str | None = None,
    tags: list[str] | None = None,
    idempotency_key: str | None = None,
    deployment_name: str = E2E_PACKET_DEPLOYMENT_NAME,
) -> dict[str, Any]:
    ...
```

`submit_e2e_packet_flow_run(...)` must:

- use the existing runtime config mechanism;
- set/use the configured Prefect API URL the same way existing submitters do;
- read deployment by name;
- create a flow run from deployment;
- return a JSON-safe dict, not a raw Prefect object;
- include the deployment name, flow run id, flow run name, queue/work-pool metadata when available.

Tags must include:

- `grace`;
- `packet`;
- `e2e`;
- `packet:{packet_id}`;
- `feature:{feature_id}`;
- `wave:{wave_id}` when available.

Do not modify existing feature submitter behavior except for harmless shared
helper extraction if needed.

### 4. Preserve Deterministic Idempotency

Keep the existing deterministic idempotency key shape:

```text
grace-packet:{project_key}:{packet_id}:attempt-{attempt}:{source_hash}
```

Rules:

- source hash must come from parsed/registry packet data;
- missing source hash must fail closed for that packet;
- same packet/attempt/source hash must not create duplicate Prefect runs;
- changed source hash may create a new idempotency key.

Do not add timestamp/random values to idempotency keys.

### 5. Registry Records Must Reflect E2E Submission

After successful E2E submission, update the packet registry record with
operator-visible run metadata:

```json
{
  "registry_status": "submitted",
  "registry_reason": "prefect_e2e_flow_run_submitted",
  "prefect_flow_run_id": "...",
  "prefect_flow_run_name": "e2e-packet:...",
  "prefect_deployment_name": "prefect-grace-e2e-packet-runner/live-e2e-packet-runner",
  "submission_runner_kind": "e2e",
  "submission_idempotency_key": "...",
  "submitted_at": "..."
}
```

Do not mark packets as `accepted`, `completed`, `blocked`, or
`cascading_blocked` in this packet except for statuses already produced by
BacklogController planning.

If submit fails, do not mutate the packet to `submitted`.

### 6. CLI `submit-packets` Must Surface The Runner Kind

Update `submit-packets` JSON/text output so operators can see which runner was
submitted.

Required JSON fields per record:

- `packet_id`;
- `flow_run_id`;
- `flow_run_name`;
- `deployment_name`;
- `runner_kind`;
- `status`;
- `idempotency_key`.

The CLI must keep safe defaults:

- dry-run by default;
- live execution only when explicit existing execute flags allow it;
- no live agent execution during tests.

If a compatibility flag is added, prefer:

```bash
--runner e2e|managed
```

Default must be `e2e`.

### 7. Runtime Adapter Must Submit E2E Runs

Update `PrefectRuntimeAdapter.submit_packet_run(...)` to use the E2E packet
submitter by default.

The adapter must not submit `prefect-grace-feature-pipeline/live-feature-pipeline`
for packet runs.

The adapter should filter/normalize known fields the same way it currently does
for compatibility, but the resulting parameters must target
`e2e_packet_runner_flow(...)`.

Unknown parameter keys should not raise `TypeError`; ignore or carry them in a
controlled metadata field if existing tests require compatibility.

### 8. No Deployment Registration In This Packet

This packet must not create or register Prefect deployments.

Allowed:

- define constants/names expected by deployment setup;
- submit through mocked submitter in tests;
- call existing Prefect client helper paths when injected/mocked.

Forbidden:

- `prefect deploy`;
- deployment YAML edits;
- work pool/queue creation;
- systemd/docker changes;
- production Prefect server mutation.

### 9. No Product Or Live-Agent Behavior Change

This packet changes only submission wiring.

Do not touch:

- backend product code;
- frontend product code;
- `feature_pipeline.py`;
- `codex_launcher.py`;
- live agent prompt/session behavior.

Tests must use fake/mocked Prefect submitters and must not call Codex, Claude,
agy, OpenRouter, OpenAI, cliproxy, Docker, backend, frontend, or a live Prefect
server.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_runtime_adapter_submit_packet_run.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_runner_flow.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP/**`

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

- Existing native submission dry-run behavior remains safe.
- Existing native submission tests continue to pass after updated expectations.
- Existing runtime adapter tests continue to pass after updated expectations.
- Existing E2E flow tests continue to pass.
- Existing CLI contract tests continue to pass.
- `submit-packets` remains dry-run by default.
- No product backend/frontend files are modified.
- No live agents, provider APIs, Docker containers, or live Prefect server calls are made by tests.
- No merge, push, squash, accept, or delete-worktree behavior is added.
- No Prefect deployment is registered or scheduled by tests.
- Idempotency keys stay deterministic and source-hash based.
- Failed submission does not mutate packet registry into `submitted`.

## Required Implementation Shape

### Native Submission

`submit_ready_packets_to_prefect(...)` should keep the same high-level contract:

```python
def submit_ready_packets_to_prefect(
    *,
    project: Any,
    dry_run: bool = True,
    limit: int | None = None,
    execute_agent: bool = False,
    timeout_seconds: int = 3600,
    base_ref: str = "HEAD",
    worktree_root: Path | None = None,
    scheduled_for: str | None = None,
    continue_on_error: bool = False,
    submitter: Callable[..., dict[str, Any]] | None = None,
    runner_kind: Literal["e2e", "managed"] = "e2e",
) -> NativeSubmissionResult:
    ...
```

If `runner_kind` is not added, the implementation must still prove by tests that
the default submitted deployment is the E2E deployment.

### Submission Record

Extend `PacketSubmissionRecord` with:

```python
runner_kind: str = "e2e"
```

If adding the field is too disruptive, include it in `to_dict()` through a
stable metadata field. Tests must assert it is visible in JSON.

### Submitter

Add E2E submitter functions in `prefect_submitter.py`; keep existing managed
submitter functions intact.

### Runtime Adapter

`PrefectRuntimeAdapter.submit_packet_run(...)` must call the E2E submitter path
by default and return a JSON-safe run reference with:

- `run_id`;
- `runtime`;
- `packet_id`;
- `feature_id`;
- `runner_kind`;
- `deployment_name`;
- `url`;
- `state`.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_runtime_adapter_submit_packet_run.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run focused regressions:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_packet_runner_flow.py \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_status_model.py \
  tests/test_prefect_grace_managed_packet_runner.py
```

Run static checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/prefect_native_submission.py \
  prefect_grace/platform/runtime_adapter.py \
  prefect_grace/tasks/prefect_submitter.py \
  prefect_grace/cli.py

python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_native_submission.py \
  prefect_grace/platform/runtime_adapter.py \
  prefect_grace/tasks/prefect_submitter.py

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI dry-run smoke in a temporary project adapter fixture:

```bash
python3 -m prefect_grace.cli submit-packets \
  --project-config /tmp/grace-native-e2e-smoke/project.yaml \
  --dry-run \
  --limit 1 \
  --json
```

Run execute-mode smoke only with an injected/fake submitter in tests. Do not
call a live Prefect server.

## Expected Evidence

Attach under `EVIDENCE/attempt-XXXX/`:

- targeted pytest output;
- focused regression pytest output;
- compile output;
- GRACE lint output;
- packet validation JSON;
- CLI dry-run smoke JSON showing `runner_kind=e2e`;
- fake submitter execute test output proving deployment name is E2E;
- `git diff --stat`;
- full changed file list;
- explicit note that no live agents, provider APIs, Prefect deployments, Docker containers, product backend/frontend services, merge, squash, or push were started by tests.

## Escalation Triggers

Stop and ask the controller if:

- implementation needs to modify `feature_pipeline.py`;
- implementation needs to modify `e2e_packet_runner.py` or `e2e_packet_runner_flow.py`;
- implementation needs to change `status_model.py`;
- implementation needs to change backlog planning semantics;
- implementation requires a live Prefect server in tests;
- implementation requires deployment registration;
- implementation requires changing live agent launch behavior;
- implementation requires product backend/frontend changes;
- failed submissions need to mark packet domain status as accepted/completed/blocked.

## Reviewer Checklist

- `submit-packets` default runner is E2E.
- Prefect deployment name is `prefect-grace-e2e-packet-runner/live-e2e-packet-runner`.
- Dry-run remains the default.
- Execute-mode tests use fake/mocked submitter only.
- Idempotency keys are unchanged and deterministic.
- Registry `submitted` metadata includes `submission_runner_kind=e2e`.
- Runtime adapter no longer submits feature pipeline for packet runs.
- No deployment registration was added.
- No live agents/providers were called in tests.
- Frozen scope is clean.
