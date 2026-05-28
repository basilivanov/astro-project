# Review 0004 — FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING

status: rework_required
reviewer: codex
source_hash: sha256:415028c5458ea4395a3d5dfb7cff4528cbc60891763b5637b01268378e096358
reviewed_commit: dca794a
attempt: attempt-0004
reviewed_at: 2026-05-28

## Verdict

Rework required.

The review-0003 blockers are mostly addressed: successful apply now re-reads
deployment after-state, stale `DEPLOYMENT_NOT_FOUND` is cleared, plain
`--apply-deployment` again produces a dry-run plan, and platform-level injected
tests were added.

However, the lower-level preflight can still report `ok=true` while an explicit
apply request is missing approval gates. CLI blocks this path before preflight
for the current command, but the platform contract must remain fail-closed
because this function is the safety boundary used by tests and future
orchestration code.

No real deployment apply was run against the live Prefect server.

## Blocker

### 1. Platform apply gate can return `ok=true` when approval is missing

`prefect_grace/platform/prefect_worker_binding.py:475-478` appends approval gate
errors:

```text
DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED
DEPLOYMENT_APPLY_NOT_APPROVED
```

But `prefect_grace/platform/prefect_worker_binding.py:515-521` excludes those
errors when calculating `ok`:

```text
len([e for e in errors if e["type"] not in [
    "DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED",
    "DEPLOYMENT_APPLY_NOT_APPROVED",
]]) == 0
```

When the deployment already exists and routes correctly, an apply request without
approval gates returns `ok=true` even though `errors` contains an approval blocker
and no apply ran.

Injected proof, with no live Prefect mutation:

```text
{'ack': False,
 'token': 'deployment',
 'ok': True,
 'deployment_mutation': 'none',
 'errors': [{'type': 'DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED', ...}],
 'runs': 0,
 'agents': 0}

{'ack': True,
 'token': None,
 'ok': True,
 'deployment_mutation': 'none',
 'errors': [{'type': 'DEPLOYMENT_APPLY_NOT_APPROVED', ...}],
 'runs': 0,
 'agents': 0}
```

This violates the packet contract that deployment registration/refresh is
allowed only when all gates are present and that missing approval must fail
closed. It also weakens the new `test_preflight_missing_approval_gates` test:
that test checks the error type, but does not assert `result.ok is False`, and it
uses a missing deployment fixture that masks the issue.

Required fix:

- approval gate errors must make the platform result `ok=false`;
- add regression coverage where the deployment already exists and is valid, but
  `apply_deployment=True`, `dry_run=False`, and either acknowledgement or env
  approval is missing;
- assert `result.ok is False`, `deployment_mutation == "none"`,
  `prefect_runs_created == 0`, and `live_agents_started == 0`;
- keep the CLI early `sys.exit(2)` guard for real `--apply --apply-deployment`
  missing gates.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `57 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`, CLI
  handler, and parser: passed.
- Strict packet validation: `ok=true`.
- Worker-container CLI dry-run: live Prefect reached, pool/queues ready,
  deployment missing, `deployment_mutation=dry_run_would_register`, zero flow
  runs and zero live agents.
- Worker-container plain `--apply-deployment` with approval env and acknowledgement:
  `deployment_mutation=dry_run_would_apply`, zero flow runs and zero live agents.
- Host CLI `--apply --apply-deployment` without acknowledgement exits `2` before
  preflight.
- Injected apply-success proof: missing deployment -> successful mocked apply ->
  deployment re-read -> `ok=true`, no stale errors, zero flow runs and zero live
  agents.
- Injected missing-approval proof against an already valid deployment demonstrates
  the blocker above.

## Required Rework

1. Make approval gate errors terminal for platform `ok`.
2. Strengthen missing-approval tests so the valid-deployment case cannot return
   `ok=true`.
3. Re-run targeted tests, compile, lint, strict packet validation, safe worker
   dry-run, and safe worker dry-run apply-plan.
