# Review 0004 - FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY

status: rework_required
reviewer: codex
source_hash: sha256:0ad3753fa62edcc89abc5d7c228bd1500080e41797ba989f929acbaa4395d6f0
reviewed_commit: 7efc82893473ddba92088244981a0708213e1800
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Rework required.

The five blockers from review-0003 are closed: `e2e_packet_runner.py` has no
net diff in this packet scope, `DeploymentApplyResult.to_dict` now has a GRACE
function contract, evidence artifacts validate, invalid-entrypoint coverage now
guards the runtime apply path, and the invalid self-approval review artifact was
removed.

One gating regression remains in the live worker-container dry-run behavior.

## Blocker

### 1. Plain `--apply-deployment` still requires env approval in dry-run mode

The packet requires plain `--apply-deployment` to remain a dry-run deployment
plan unless the explicit mutation flag and approval gates are present:

```text
Plain `--apply-deployment` must remain a dry-run plan unless the mutation flag
and approval gates are present.
```

Observed command, with no `--apply` and no real mutation approval env:

```bash
docker compose -f docker-compose.yml -f docker-compose.grace-worker.yml \
  --profile grace-worker run --rm --no-deps grace_worker \
  python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --apply-deployment \
  --i-understand-prefect-mutation \
  --json
```

Observed output:

```json
{
  "dry_run": true,
  "deployment_mutation": "none",
  "prefect_runs_created": 0,
  "live_agents_started": 0,
  "errors": [
    {
      "type": "DEPLOYMENT_APPLY_NOT_APPROVED",
      "message": "Deployment apply requires GRACE_PREFECT_BINDING_APPROVED=deployment"
    }
  ]
}
```

With `GRACE_PREFECT_BINDING_APPROVED=deployment`, the same dry-run command
reports the expected plan:

```json
{
  "dry_run": true,
  "deployment_mutation": "dry_run_would_apply",
  "prefect_runs_created": 0,
  "live_agents_started": 0
}
```

That means the dry-run plan path is incorrectly dependent on the real mutation
approval token. The CLI layer already enforces approval gates only for
`--apply-deployment --apply`; the platform preflight should match that contract.

Required fix:

- only require `--i-understand-prefect-mutation` and
  `GRACE_PREFECT_BINDING_APPROVED=deployment` when `dry_run is False` and
  `apply_deployment is True`;
- keep missing gates fail-closed for real apply mode;
- add a platform regression for `dry_run=True`, `apply_deployment=True`, and no
  approval token returning `deployment_mutation="dry_run_would_apply"` with zero
  runs and zero live agents;
- add or strengthen CLI coverage proving plain `--apply-deployment` without
  env approval still reaches the dry-run plan.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `60 passed`.
- `timeout 90s pytest -q tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_e2e_packet_runner_flow.py`: `17 passed`; no live Codex verifier process observed.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`,
  `cli_commands/prefect_worker_binding.py`, and `cli_commands/parser.py`: passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`, `evidence_count=8`, eight artifacts
  validated. The manifest still emits `unknown_evidence_id` warnings because
  the packet lists prose evidence names rather than strict IDs; this is not a
  blocker now that artifact validation is non-empty and clean.
- Scope check against `d060a1d..HEAD`: `ok=true`, `outside_allowed=[]`,
  `frozen_violations=[]`.
- Worker-container dry-run binding: reaches live Prefect server, pool, and
  queues; deployment missing is expected before real apply; zero flow runs and
  zero live agents.
- Persistent worker check after docker dry-runs: no `astro-project-grace_worker`
  container left running.

## Observability Verdict

degraded-but-expected.

The live worker-container checks reached Prefect and confirmed zero flow runs
and zero live agents. The degradation is expected because the managed deployment
has not been applied yet. The blocker is limited to dry-run plan gating, not to
unexpected side effects.
