# Review 0001 — FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE

status: rework_required
reviewer: codex
source_hash: sha256:6cc10e3ca7c7f929936c2604f3b46dafa3510035267a48d8645d286dc24abfb2
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

The packet is close, but the smoke still accepts destructive roots that are not
constrained to a dedicated throwaway namespace. As written, `_validate_roots()`
allows `state_root=/opt/astro-project`, and `_reset_temp_runtime_roots()` then
calls `shutil.rmtree(state_root, ignore_errors=True)`. That is too risky for a
command that claims to require explicit temporary roots.

## Blockers

### 1. `state_root` / `worktree_root` are still too permissive for destructive cleanup

`prefect_grace/platform/e2e_runner_registry_seeded_smoke.py:259-280` only
rejects runtime paths and repo-contained `worktree_root` / `packet_root`
values. It does not reject a broad `state_root` such as the repository root, a
shared temp root, or another caller-controlled directory. The reset helper at
`prefect_grace/platform/e2e_runner_registry_seeded_smoke.py:276-280` then
deletes whatever path was supplied.

I checked the validator directly: `_validate_roots(..., state_root=Path('/opt/astro-project'), ...)`
returns `[]`.

Required fix:

- require all three roots to be explicit throwaway temp roots, or derive child
  directories from one validated smoke base;
- never `rmtree()` a user-supplied root unless it has been proven to be a
  generated smoke directory;
- add regression tests that fail closed for broad-root inputs such as
  `state_root=PROJECT_ROOT`, `worktree_root=/tmp`, and `packet_root=/tmp` (or
  equivalent safe broad-root cases).

## Non-Blocking Notes

- The rest of the packet shape is aligned with the execution packet: one
  selected child, zero Prefect runs, and bounded temp-only writes.
- `python3 scripts/grace_lint.py prefect_grace/cli.py` still reports existing
  CLI-wide contract debt unrelated to this packet; the new smoke module itself
  passes targeted lint.
- Post-test observability on the smoke run is
  `degraded-but-expected` because the synthetic corpus intentionally contains
  fixture warnings for review and missing-dependency cases.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_e2e_runner_registry_seeded_smoke.py tests/test_prefect_grace_cli_e2e_runner_registry_seeded_smoke.py tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_cli_e2e_packet_runner.py tests/test_prefect_grace_cli_contracts.py`: `49 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`: passed.
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/EXECUTION_PACKET.md --strict --json`: `ok=true`, `warnings=0`, `errors=0`.
- `python3 -m prefect_grace.cli run-e2e-registry-seeded-smoke --json`: `ok=true`,
  `selected_packet_id=SMOKE-CHILD-RUNNABLE-W01-PACKET`,
  `bootstrap_apply_count=6`,
  `prefect_runs_created=0`,
  `live_agents_started=0`,
  `writes_outside_temp_roots=[]`,
  `errors=[]`.

## Required Rework

1. Tighten root validation so destructive cleanup can only happen under a
   dedicated synthetic temp namespace.
2. Add regression coverage for broad-root rejection.
3. Re-run the packet tests, strict validation, and smoke command.
4. Resubmit for review.
