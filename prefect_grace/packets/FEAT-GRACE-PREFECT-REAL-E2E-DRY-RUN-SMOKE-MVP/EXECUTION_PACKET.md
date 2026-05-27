# Execution Packet: FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP-W01-REAL-E2E-DRY-RUN-SMOKE

- packet_id: FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP-W01-REAL-E2E-DRY-RUN-SMOKE
- feature_id: FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP
- wave_id: W01
- status: ready
- phase: PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP
- depends_on: FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP-W01-E2E-LIVE-SMOKE, FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP-W01-BATCH-E2E-QUEUE-SMOKE

## Objective

Add the first controlled real Prefect E2E dry-run smoke for the portable GRACE
packet runner.

The smoke must submit exactly one scratch-only packet to the real Prefect
`prefect-grace-e2e-packet-runner/live-e2e-packet-runner` deployment and verify
that the flow run is created and reaches an operator-visible terminal or
accepted dry-run state. It must not use the offline fake submitter, must not run
live agents, and must not touch product backend/frontend code.

## Why This Exists

The previous packets proved:

- single-packet E2E submission with an offline fake submitter;
- bounded batch E2E queue submission with an offline fake submitter;
- deployment wiring for the E2E packet runner.

This packet closes the next gap: prove that the same path works against the real
Prefect server/worker/queue while keeping agent execution disabled.

This is the last safety layer before a single live-agent scratch smoke.

## GRACE Canon Context

- Runtime: Prefect is an adapter, not GRACE core.
- Runner: E2E packet runner is the current portable packet execution path.
- Safety: real Prefect is allowed; live Codex/Claude/agy execution is not.
- State: scratch smoke state/worktrees/packets must be isolated from production packet state.
- Verification: Prefect run existence and terminal/dry-run result must be observable without SSH tailing.

## Architecture Constraints

### Required behavior

Implement a controlled real dry-run smoke harness:

```python
run_prefect_e2e_real_dry_run_smoke(...)
```

It must:

1. generate exactly one strict scratch-only packet;
2. write it under an isolated `packet_root`;
3. seed it into an isolated registry under `state_root`;
4. call existing native submission primitives with:
   - `runner_kind="e2e"`;
   - `dry_run=False` for submission planning itself;
   - E2E flow parameter `dry_run=True`;
   - E2E flow parameter `execute_agent=False`;
   - `limit=1`;
5. use the real `E2EPacketSubmitter` by default;
6. optionally wait for the Prefect flow run status via existing runtime adapter/status reader;
7. return a JSON-safe result with run metadata, status, deployment, queue, packet id, and errors.

### Required CLI

Add:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-real-dry-run-smoke \
  --project-config prefect_grace/project.yaml \
  --state-root /tmp/grace-real-e2e-smoke/state \
  --worktree-root /tmp/grace-real-e2e-smoke/worktrees \
  --packet-root /tmp/grace-real-e2e-smoke/packets \
  --timeout-seconds 900 \
  --json
```

CLI requirements:

- `--project-config` required;
- `--state-root` required;
- `--worktree-root` required;
- `--packet-root` required;
- `--timeout-seconds` default `900`;
- `--poll-interval-seconds` default `5`;
- `--no-wait` optional, only verifies run creation;
- `--execute-agent` must be rejected fail-closed;
- no `--offline-fake-submitter` in this command.

### Result model

Return JSON-safe result similar to:

```json
{
  "ok": true,
  "mode": "prefect_real_e2e_agent_dry_run",
  "packet_id": "FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP-W01-REAL-E2E-DRY-RUN-SMOKE",
  "runner_kind": "e2e",
  "deployment_name": "prefect-grace-e2e-packet-runner/live-e2e-packet-runner",
  "work_queue_name": "grace-live",
  "flow_run_id": "...",
  "flow_run_name": "...",
  "flow_run_url": "...",
  "submitted": true,
  "prefect_state_type": "completed",
  "prefect_state_name": "Completed",
  "domain_status": "accepted|check_passed|runner_error|unknown",
  "artifact_ids": [],
  "errors": []
}
```

`ok=true` requires:

- exactly one record submitted;
- deployment name is the E2E packet runner deployment;
- run id exists;
- if waiting is enabled, Prefect state is terminal successful or the E2E result indicates accepted/check-passed dry-run domain status.

If waiting times out, return `ok=false` with:

```json
{"code": "PREFECT_DRY_RUN_TIMEOUT", "message": "..."}
```

Do not hide timeout by returning success.

## Allowed Write Scope

- `prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py`
- `prefect_grace/cli.py`
- `tests/test_prefect_grace_prefect_e2e_real_dry_run_smoke.py`
- `tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP/**`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `prefect_grace/platform/prefect_native_submission.py`
- `prefect_grace/platform/runtime_adapter.py`
- `prefect_grace/tasks/prefect_submitter.py`
- `prefect_grace/deploy_live.py`
- `prefect_grace/flows/e2e_packet_runner_flow.py`
- `prefect_grace/platform/e2e_packet_runner.py`
- `prefect_grace/platform/prefect_e2e_live_smoke.py`
- `prefect_grace/platform/prefect_e2e_batch_smoke.py`
- `prefect_grace/tasks/e2e_packet_artifacts.py`
- `prefect_grace/tasks/codex_launcher.py`
- `scripts/grace_lint.py`
- `scripts/pipeline.py`
- `scripts/run_e2e.sh`
- `docker-compose*.yml`
- `.env`

## Must Preserve

- Existing fake-submitter live smoke behavior.
- Existing batch smoke behavior.
- Existing native E2E submission behavior.
- Existing deployment names.
- Existing E2E runner flow parameters.
- No product backend/frontend changes.
- No live agent execution.
- No batch execution in this packet.
- No merge, push, squash, commit, or deployment mutation from the smoke harness.

## Required Safety Guards

- `--execute-agent` must fail before submission.
- The generated packet's allowed scope must be only `scratch/grace-real-e2e-smoke/**`.
- The generated packet's frozen scope must include `prefect_grace/**`, `backend/**`, `frontend/**`, `.env`, `scripts/**`, `tools/**`, and `docker-compose*.yml`.
- The harness must refuse to proceed if native submission plans more than one packet.
- The harness must refuse unexpected deployment names.
- The harness must not mutate existing real packet registry/state unless explicitly given those paths by operator.

## Implementation Notes

Preferred module shape:

```python
@dataclass(frozen=True)
class PrefectE2ERealDryRunSmokeResult:
    ok: bool
    mode: str
    packet_id: str
    runner_kind: str
    deployment_name: str
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
    errors: list[dict[str, Any]]
```

Do not introduce a new runtime adapter in this packet. Use existing submission
and status-reading primitives if available. If status reading needs a small
wrapper, keep it inside the new smoke module and do not modify
`runtime_adapter.py`.

## Verification

The worker must run the offline/unit tests, focused regressions, static checks, and the real Prefect smoke when Prefect server and worker are available.

### Offline/unit tests

Run:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_e2e_real_dry_run_smoke.py \
  tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py \
  tests/test_prefect_grace_cli_contracts.py
```

Required tests:

- smoke builds exactly one scratch packet;
- `--execute-agent` is rejected before submission;
- unexpected packet count is rejected;
- unexpected deployment is rejected;
- no-wait mode succeeds after run creation;
- wait mode handles completed state;
- wait mode times out with `PREFECT_DRY_RUN_TIMEOUT`;
- CLI help exposes required flags;
- CLI JSON envelope is stable.

### Focused regressions

Run:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_e2e_live_smoke.py \
  tests/test_prefect_grace_prefect_e2e_batch_smoke.py \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_e2e_packet_runner_flow.py
```

### Static checks

Run:

```bash
python3 -m compileall -q \
  prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py \
  prefect_grace/cli.py

python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP/EXECUTION_PACKET.md \
  --strict --json
```

### Real Prefect smoke

If Prefect server and worker are available, run exactly once:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-real-dry-run-smoke \
  --project-config prefect_grace/project.yaml \
  --state-root /tmp/grace-real-e2e-smoke/state \
  --worktree-root /tmp/grace-real-e2e-smoke/worktrees \
  --packet-root /tmp/grace-real-e2e-smoke/packets \
  --timeout-seconds 900 \
  --json
```

Expected:

- one Prefect flow run is created;
- deployment name is `prefect-grace-e2e-packet-runner/live-e2e-packet-runner`;
- `execute_agent=false` in parameters;
- flow reaches success/dry-run accepted state, or a clear timeout/error is returned;
- Prefect UI shows meaningful run name with packet id.

If Prefect is unavailable in the coder environment, do not fake this verification.
Record it as `not_run_prefect_unavailable` and keep offline/unit tests strict.

## Expected Evidence

Attach under `EVIDENCE/attempt-0001/`:

- `evidence_manifest.json` with command results;
- targeted pytest output;
- focused regression output;
- compileall output;
- grace_lint output;
- strict packet validation output;
- CLI help output;
- no-wait fake status-reader smoke output;
- real Prefect smoke output if available;
- explicit note whether live Prefect was or was not run;
- explicit note that live agents were not run.

## Review Checklist

Reviewer must verify:

- no fake submitter exists in this command;
- no live agent execution path is possible;
- exactly one packet can be submitted;
- deployment name is E2E packet runner;
- timeout returns failure, not success;
- generated packet write scope is scratch-only;
- frozen scope was preserved;
- product backend/frontend were untouched.

## Escalation Triggers

STOP and ask controller if:

- implementation needs to modify `runtime_adapter.py`;
- implementation needs to modify `prefect_submitter.py`;
- implementation needs to modify E2E flow parameters;
- smoke requires live agent execution;
- smoke needs more than one packet;
- smoke needs product backend/frontend writes;
- Prefect deployment is missing and cannot be submitted without changing deployment wiring.

## Evidence

Pending implementation.

## Reviewer Notes

Pending review.
