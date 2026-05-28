# Review 0005 — FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING

status: accepted
reviewer: codex
source_hash: sha256:415028c5458ea4395a3d5dfb7cff4528cbc60891763b5637b01268378e096358
reviewed_commit: 83c964d
attempt: attempt-0005
reviewed_at: 2026-05-28

## Verdict

Accepted.

The review-0004 blocker is fixed. Approval gate errors are now terminal for
platform `ok`, including the case where the managed deployment already exists
and routes correctly. The prior review blockers also remain closed:

- successful approved apply re-reads deployment after-state and clears stale
  pre-apply `DEPLOYMENT_NOT_FOUND`;
- plain `--apply-deployment` remains a dry-run plan unless `--apply` is present;
- platform-level injected tests cover dry-run planning, successful apply,
  failed apply, and missing approval gates.

No real deployment apply was run against the live Prefect server.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `58 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`, CLI
  handler, and parser: passed.
- Strict packet validation: `ok=true`.
- Injected missing-approval proof against a valid deployment:
  `ok=false`, `deployment_mutation=none`, `prefect_runs_created=0`,
  `live_agents_started=0`.
- Injected approved apply proof:
  missing deployment -> mocked apply success -> deployment re-read ->
  `ok=true`, no stale errors, zero flow runs and zero live agents.
- Worker-container CLI dry-run:
  live Prefect reached, `astro-process`, `grace-live`, and `grace-monitoring`
  ready; managed deployment missing; `deployment_mutation=dry_run_would_register`;
  zero flow runs and zero live agents.
- Worker-container plain `--apply-deployment` with approval env and
  acknowledgement:
  `deployment_mutation=dry_run_would_apply`; zero flow runs and zero live agents.
- Host CLI real apply missing acknowledgement exits code `2` before preflight.
- `./scripts/grace_worker_smoke.sh`: passed with Prefect `3.6.25`; no persistent
  `grace_worker` container remained running.

## Residual Notes

- The live managed packet runner deployment is still absent in the current
  Prefect server. This is expected because real deployment apply was intentionally
  not run during review.
- The next packet may perform the approved deployment apply under explicit
  Architect approval, with the existing guardrails preserved.
