# Review 0005 - FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY

status: accepted
reviewer: codex
source_hash: sha256:0ad3753fa62edcc89abc5d7c228bd1500080e41797ba989f929acbaa4395d6f0
reviewed_commit: 710d5dc
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Accepted.

The blocker from review-0004 is fixed. Plain `--apply-deployment` now remains a
dry-run deployment plan without requiring real mutation approval gates, while
real `--apply --apply-deployment` still fails closed unless the approval env is
present.

No real deployment apply was run during review.

## Reviewed Behavior

- Dry-run binding without `GRACE_PREFECT_BINDING_APPROVED=deployment` now
  returns `deployment_mutation="dry_run_would_apply"`.
- Dry-run plan still reports `prefect_runs_created=0` and
  `live_agents_started=0`.
- Real apply without env approval exits fail-closed before mutation.
- The previous `e2e_packet_runner.py` safety regression remains absent from the
  final packet diff and dry-run E2E regression is green.
- Worker smoke is green and leaves no persistent `grace_worker` container.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `62 passed`.
- `timeout 90s pytest -q tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_e2e_packet_runner_flow.py`: `17 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`,
  `cli_commands/prefect_worker_binding.py`, and `cli_commands/parser.py`: passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`, eight artifacts validated. The
  manifest keeps `unknown_evidence_id` warnings because the packet lists prose
  evidence names rather than strict IDs; this is not blocking.
- Scope check against `d060a1d..HEAD`: `ok=true`, `outside_allowed=[]`,
  `frozen_violations=[]`.
- Worker-container dry-run plan without env approval:
  `deployment_mutation="dry_run_would_apply"`, `prefect_runs_created=0`,
  `live_agents_started=0`.
- Worker-container real apply without env approval exits with code `2` and
  reports `--apply-deployment requires GRACE_PREFECT_BINDING_APPROVED=deployment`.
- `./scripts/grace_worker_smoke.sh`: `prefect=3.6.25`,
  `grace worker smoke: ok`.
- Persistent worker check after smoke: no `astro-project-grace_worker` container
  left running.

## Observability Verdict

degraded-but-expected.

The live-adjacent checks reached the Prefect server, work pool, and queues.
The deployment is still missing because real deployment apply was intentionally
not run without Architect approval. No Prefect flow runs, live agents, registry
writes, source packet writes, Git mutations, backend/frontend changes, or
persistent workers were created by this review.
