# Execution Packet: GRACE E2E Prefect Flow Wiring MVP

## Objective

Expose the accepted deterministic `run_e2e_packet(...)` orchestration path as a
Prefect-visible flow with operator artifacts.

The current platform can run a full single-packet E2E chain from CLI/platform
code:

```text
managed packet runner
→ worktree/scope lifecycle
→ verifier/reviewer handoff
→ domain status
→ registry transition fields
```

But Prefect still has only lower-level flow visibility for managed packet /
scope lifecycle paths. This packet adds the thin Prefect wrapper for the full
E2E runner so operators can inspect one complete GRACE packet run in Prefect
before batch submission is rewired to use it.

This packet must not change scheduling, backlog planning, native submission,
deployment registration, live agent defaults, or the large legacy
`feature_pipeline.py`.

## Slice

- slice_id: `SLICE-GRACE-E2E-PREFECT-FLOW-WIRING-MVP`
- slice_slug: `grace-e2e-prefect-flow-wiring-mvp`
- feature_id: `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP`
- packet_id: `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP-W01-E2E-PACKET-RUNNER, FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP-W01-E2E-STATUS-TRANSITION, FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP-W01-PREFECT-LIFECYCLE-FLOW`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/prefect_grace/flows/verifier_reviewer_handoff_flow.py`
- `/opt/astro-project/prefect_grace/tasks/managed_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/handoff_artifacts.py`
- `/opt/astro-project/prefect_grace/prefect_compat.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-E2E-PREFECT-FLOW`
- `M-GRACE-PREFECT-ARTIFACTS`
- `M-GRACE-CLI`
- `M-GRACE-STATUS-MODEL`

## Recommended Role Assignment

- context collector: `Haiku` or equivalent cheap model, optional, to inspect existing Prefect flow/artifact/CLI patterns.
- coder: `Sonnet high` or `Codex high`; deterministic flow/task/CLI wiring, no live agent logic.
- verifier: `Codex medium`; must run offline flow tests, artifact tests, CLI smoke, and status-model regressions.
- reviewer: `Codex xhigh` or `Opus`; must verify no batch submission/deployment/live-agent semantics slipped in.
- rework policy: fresh context for flow/status semantics changes; light resume only for CLI names, artifact markdown wording, or import fixes.

## Required Design Decisions

### 1. Add A Dedicated E2E Prefect Flow

Add a new module:

```text
prefect_grace/flows/e2e_packet_runner_flow.py
```

Required flow:

```python
@flow(
    name="prefect-grace-e2e-packet-runner",
    flow_run_name="e2e-packet:{packet_id}:attempt-{attempt}",
)
def e2e_packet_runner_flow(
    *,
    project_root: str,
    packet_path: str,
    state_root: str,
    worktree_root: str,
    project_key: str,
    packet_id: str,
    attempt: int = 1,
    base_ref: str = "HEAD",
    dry_run: bool = True,
    execute_agent: bool = False,
    fake_verifier_output: str | None = None,
    fake_reviewer_output: str | None = None,
    timeout_seconds: int = 3600,
    keep_worktree: bool = True,
) -> dict[str, Any]:
    ...
```

Required tasks:

- `run_e2e_packet_task(...)`;
- `publish_e2e_packet_artifact_task(...)`.

The task must call the existing `run_e2e_packet(...)` function. It must not
reimplement worktree creation, scope validation, handoff parsing, or registry
transition mapping.

### 2. Preserve Domain Outcomes As Flow Results

The flow should normally complete as a Prefect run for deterministic domain
outcomes:

- `accepted`;
- `rework_required`;
- `blocked`;
- `scope_blocked`;
- `agent_failed`;
- `verifier_failed`;
- `reviewer_failed`;
- `handoff_error`;
- `runner_error`.

These are GRACE domain outcomes, not Python exceptions. Unexpected programming
errors may still fail the Prefect run.

The returned dict must include at minimum:

```json
{
  "ok": false,
  "packet_id": "...",
  "runtime_status": "completed",
  "domain_status": "rework_required",
  "registry_status": "ready_for_retry",
  "registry_reason": "quality_rework",
  "registry_transition": {
    "registry_status": "ready_for_retry",
    "reason": "quality_rework"
  },
  "artifact_ids": []
}
```

Do not invent new status strings. Use the serialized values already returned by
`run_e2e_packet(...)`.

### 3. Publish Operator Artifact

Add a small dedicated artifact helper:

```text
prefect_grace/tasks/e2e_packet_artifacts.py
```

Required public function:

```python
def publish_e2e_packet_run_artifact(result: dict[str, Any]) -> list[str]:
    ...
```

Artifact markdown must include:

- packet id;
- attempt;
- runtime status;
- domain status;
- registry status;
- registry reason;
- worktree path;
- executor id;
- managed runner status;
- handoff status;
- artifact paths;
- errors;
- blocker/rework reason when present.

Artifact publication is best-effort:

- if Prefect artifacts are unavailable, return `[]`;
- if artifact publication fails, return `[]`;
- do not hide or mutate the domain result.

Prefer lazy/importlib-based Prefect imports if needed, matching the existing
artifact helper style. Do not modify `scripts/grace_lint.py` to make imports
pass.

### 4. Add A Local CLI Flow Runner

Add a CLI command:

```bash
python3 -m prefect_grace.cli run-e2e-packet-flow \
  --project-root /opt/astro-project \
  --packet prefect_grace/packets/.../EXECUTION_PACKET.md \
  --state-root /tmp/grace-state \
  --worktree-root /tmp/grace-worktrees \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --fake-verifier-output /tmp/verifier.md \
  --fake-reviewer-output /tmp/reviewer.md \
  --json
```

The command may call the flow function directly. Tests must not require a live
Prefect server.

CLI exit codes:

- `0` when `domain_status=accepted`;
- `1` when the flow returns a non-accepted GRACE domain outcome;
- `2` for command/input/runtime errors.

JSON output must include `ok`, `domain_status`, `registry_status`,
`registry_reason`, `registry_transition`, `packet_id`, `attempt`, and
`artifact_ids`.

Text output must show:

- packet id;
- domain status;
- registry status;
- registry reason;
- artifact ids count.

### 5. Keep Batch Submission Out Of Scope

This packet must not change:

- `submit-packets`;
- `submit_ready_packets_to_prefect(...)`;
- `PrefectRuntimeAdapter.submit_packet_run(...)`;
- `prefect_grace/tasks/prefect_submitter.py`;
- deployment names;
- work pool / queue config;
- idempotency-key policy.

The next packet will switch native submission from managed-only runs to E2E
flow runs. This packet only creates and tests the flow seam.

### 6. No Deployment Registration

This packet must not register a Prefect deployment or schedule runs.

Allowed:

- define the flow function;
- call it directly in tests/CLI;
- publish best-effort artifacts when a Prefect runtime is available.

Forbidden:

- `prefect deploy`;
- deployment YAML edits;
- work pool/queue creation;
- systemd/docker changes;
- production Prefect server mutation.

### 7. No Live Agent By Default

The flow and CLI must preserve existing safe defaults:

- `dry_run=True`;
- `execute_agent=False`;
- fake verifier/reviewer outputs for tests;
- no live Codex/Claude/agy/OpenRouter/OpenAI/cliproxy calls in tests.

If the CLI exposes `--execute-agent`, it must require explicit
`--no-dry-run --execute-agent`, matching existing runner safety behavior.

### 8. GRACE Canon Discipline

New modules must include:

- `AI_HEADER`;
- `START_MODULE_CONTRACT` / `END_MODULE_CONTRACT`;
- `START_MODULE_MAP` / `END_MODULE_MAP`;
- function contracts for public flow/task/helper functions.

Flow/task wrappers should remain small. Large orchestration logic belongs in
`prefect_grace/platform/e2e_packet_runner.py`, not in the Prefect flow module.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/e2e_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/cli.py`

Narrow integration changes if required:

- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_runner_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_artifacts.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/prefect_grace/flows/verifier_reviewer_handoff_flow.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/managed_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/handoff_artifacts.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing E2E packet runner tests continue to pass.
- Existing status model tests continue to pass.
- Existing managed packet runner tests continue to pass.
- Existing verifier/reviewer handoff tests continue to pass.
- Existing CLI command contracts continue to pass.
- No product backend/frontend files are modified.
- No live agents or provider APIs are called by tests.
- No merge/push/squash/delete-worktree operation happens.
- No Prefect deployment is registered or submitted.
- Core `run_e2e_packet(...)` remains usable without Prefect.
- Artifact publication failures do not change `domain_status`, `registry_status`, `registry_reason`, `registry_transition`, or `ok`.

## Required Implementation Shape

### Flow Module

`prefect_grace/flows/e2e_packet_runner_flow.py` should mirror the existing thin
flow wrapper pattern:

```python
@task(name="run-e2e-packet")
def run_e2e_packet_task(...) -> dict[str, Any]:
    result = run_e2e_packet(...)
    return result.to_dict()


@task(name="publish-e2e-packet-artifact")
def publish_e2e_packet_artifact_task(result: dict[str, Any]) -> list[str]:
    return publish_e2e_packet_run_artifact(result)


@flow(...)
def e2e_packet_runner_flow(...) -> dict[str, Any]:
    result = run_e2e_packet_task(...)
    artifact_ids = publish_e2e_packet_artifact_task(result)
    result["artifact_ids"] = artifact_ids
    return result
```

### Artifact Helper

`prefect_grace/tasks/e2e_packet_artifacts.py` must be independent enough to test
without a Prefect server. Use monkeypatch/fake artifact functions in tests.

Do not import Prefect artifacts at module import time if that breaks offline
tests or lint expectations.

### CLI

The CLI command should follow the existing JSON envelope pattern:

```json
{
  "ok": true,
  "command": "run-e2e-packet-flow",
  "result": {
    "packet_id": "...",
    "domain_status": "accepted",
    "registry_status": "accepted",
    "registry_reason": "execution_accepted",
    "artifact_ids": []
  }
}
```

The command must support `--json` and deterministic text output.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_packet_runner_flow.py \
  tests/test_prefect_grace_e2e_packet_artifacts.py \
  tests/test_prefect_grace_cli_e2e_packet_flow.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run focused regressions:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_status_model.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_verifier_reviewer_handoff.py
```

Run static checks:

```bash
python3 -m compileall -q \
  prefect_grace/flows/e2e_packet_runner_flow.py \
  prefect_grace/tasks/e2e_packet_artifacts.py \
  prefect_grace/cli.py

python3 scripts/grace_lint.py \
  prefect_grace/flows/e2e_packet_runner_flow.py \
  prefect_grace/tasks/e2e_packet_artifacts.py

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke in a temporary git repository with fake verifier/reviewer output:

```bash
python3 -m prefect_grace.cli run-e2e-packet-flow \
  --project-root /tmp/grace-e2e-flow-smoke/repo \
  --packet /tmp/grace-e2e-flow-smoke/repo/prefect_grace/packets/SMOKE/EXECUTION_PACKET.md \
  --state-root /tmp/grace-e2e-flow-smoke/state \
  --worktree-root /tmp/grace-e2e-flow-smoke/worktrees \
  --project-key smoke \
  --packet-id SMOKE-W01-E2E-FLOW \
  --attempt 1 \
  --base-ref HEAD \
  --fake-verifier-output /tmp/grace-e2e-flow-smoke/verifier.md \
  --fake-reviewer-output /tmp/grace-e2e-flow-smoke/reviewer.md \
  --json
```

The smoke output must include `domain_status`, `registry_status`,
`registry_reason`, and `artifact_ids`.

## Expected Evidence

Attach under `EVIDENCE/attempt-XXXX/`:

- targeted pytest output;
- focused regression pytest output;
- compile output;
- GRACE lint output;
- packet validation JSON;
- CLI smoke JSON;
- `git diff --stat`;
- full changed file list;
- explicit note that no live agents, provider APIs, Prefect deployments, Docker containers, product backend/frontend services, merge, squash, or push were started by tests.

## Escalation Triggers

Stop and ask the controller if:

- implementation needs to modify `submit-packets`, native submission, runtime adapter, or Prefect submitter code;
- implementation needs a live Prefect server in tests;
- implementation requires changing `status_model.py`;
- implementation requires changing `managed_packet_runner.py`, `verifier_reviewer_handoff.py`, or `worktree_scope_lifecycle.py`;
- implementation requires changing `feature_pipeline.py` or `codex_launcher.py`;
- artifact publication failure would need to fail the domain result;
- live Codex/Claude/agy/provider execution appears necessary;
- deployment registration appears necessary.

## Reviewer Checklist

- Flow wrapper is thin and delegates to `run_e2e_packet(...)`.
- Artifact helper is best-effort and independently testable.
- JSON/text CLI output exposes domain and registry statuses.
- `accepted` is the only success exit path.
- Non-accepted domain outcomes complete as domain results, not Python errors.
- No batch submission or deployment behavior was added.
- No live agents/providers were called in tests.
- Frozen scope is clean.
