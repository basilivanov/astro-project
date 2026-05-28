# Review 0001 - FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:3ceefd97e17f636c6c8b49326fc885c9aa6d319917dd94c1758fccc4a1ef6ed9
reviewed_commit: cd9a9bd
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The candidate-filtering unit tests pass, but the packet does not yet implement
the operator CLI path and the real dry-run/submission path is not wired to the
existing GRACE submission APIs. This means the packet cannot satisfy the first
Astro packet pilot contract yet.

No real live agent or Prefect flow run was started during review.

## Blockers

1. CLI command and CLI contract are missing.

   The execution packet requires "a single Astro pilot module and CLI command"
   and lists `tests/test_prefect_grace_cli_single_astro_packet_pilot.py` in the
   verification profile (`EXECUTION_PACKET.md:108` and
   `EXECUTION_PACKET.md:129`). The implementation only adds the platform module
   and platform tests. There is no parser registration, no command handler, no
   CLI facade export, and no CLI test file. The packet-specified pytest command
   fails before running tests:

   ```text
   ERROR: file or directory not found: tests/test_prefect_grace_cli_single_astro_packet_pilot.py
   ```

   Required fix: add the CLI command, JSON envelope contract, CLI tests, and
   CLI contract coverage.

2. Real dry-run cannot load the registry.

   `run_single_astro_packet_pilot()` calls `_load_registry_map(adapter)`
   (`prefect_grace/platform/single_astro_packet_pilot.py:286`), but the imported
   helper expects a `Path` state root and reads `state_root / "state" /
   "packet_registry.yaml"` (`prefect_grace/platform/live_opt_in_single_scratch_packet.py:270`).
   A real dry-run with `prefect_grace/project.yaml` fails before candidate
   selection:

   ```text
   ok=False
   errors=[{"code": "REGISTRY_LOAD_FAILED", "message": "unsupported operand type(s) for /: 'ProjectAdapterConfig' and 'str'"}]
   ```

   Required fix: load the runtime registry through the correct state root/store
   or use an existing project-aware API. Add a real dry-run regression that does
   not monkeypatch `_load_registry_map`.

3. Real Prefect submission path calls `submit_ready_packets_to_prefect()` with
   the wrong API.

   The implementation calls:

   ```python
   submit_ready_packets_to_prefect(
       project_key=project_key,
       packet_ids=[selected_packet_id],
       deployment_name=MANAGED_PACKET_DEPLOYMENT_NAME,
       work_queue_name=None,
       dry_run=dry_run,
   )
   ```

   at `prefect_grace/platform/single_astro_packet_pilot.py:431`, but the actual
   function requires `project`, `dry_run`, `limit`, `execute_agent`,
   `worktree_root`, `submitter`, and `runner_kind`
   (`prefect_grace/platform/prefect_native_submission.py:309`). This path will
   raise `TypeError` instead of submitting/planning one managed packet.

   Required fix: reuse the same managed submission path as the accepted scratch
   Prefect pilot: pass a project adapter, `limit=1`, `execute_agent`,
   `worktree_root`, `runner_kind="managed"`, and an injected/real submitter as
   appropriate.

4. Submission records are handled as dicts, but real records are dataclasses.

   The code reads `record.get("flow_run_id")`
   (`prefect_grace/platform/single_astro_packet_pilot.py:477`), while real
   `NativeSubmissionResult.records` contains `PacketSubmissionRecord`
   dataclasses (`prefect_grace/platform/prefect_native_submission.py:43`). An
   injected dataclass-shaped record reproduces the failure:

   ```text
   AttributeError: 'Rec' object has no attribute 'get'
   ```

   Required fix: serialize records through `to_dict()` or use an existing helper
   like the scratch pilot does, and add a regression with dataclass records.

5. Required behavioral coverage is incomplete.

   The execution packet requires tests for dry-run, missing approval, broad
   scope rejection, missing review/evidence handling, injected live success,
   injected scope blocked, and no Git mutation (`EXECUTION_PACKET.md:111`).
   Current tests stop at low-risk filtering, missing approval, explicit packet
   not found/not low-risk, and no-candidate cases
   (`tests/test_prefect_grace_single_astro_packet_pilot.py:329`). There is no
   coverage for missing review/evidence handling, injected live success, injected
   scope blocked, or no Git mutation.

   Required fix: add those regressions before accepting the pilot.

6. Evidence bundle is missing.

   The packet currently contains only `EXECUTION_PACKET.md`; there is no
   `EVIDENCE/attempt-*` directory or evidence manifest. The expected evidence in
   the packet includes strict validation, targeted pytest, compile, lint, dry-run
   candidate proof, missing approval proof, injected live proof, and no-mutation
   confirmation (`EXECUTION_PACKET.md:139`).

   Required fix: add bounded attempt evidence after the implementation blockers
   are fixed.

## Verification Reviewed

- Packet-specified pytest profile: failed because
  `tests/test_prefect_grace_cli_single_astro_packet_pilot.py` does not exist.
- `pytest -q tests/test_prefect_grace_single_astro_packet_pilot.py`: `13 passed`.
- `pytest -q tests/test_prefect_grace_cli_contracts.py`: `32 passed`.
- `python3 -m compileall -q prefect_grace/platform/single_astro_packet_pilot.py tests/test_prefect_grace_single_astro_packet_pilot.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/single_astro_packet_pilot.py`: passed.
- Strict packet validation: `ok=true`.
- Scope check against `9213d37..cd9a9bd`: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`.
- Direct real dry-run proof: `REGISTRY_LOAD_FAILED` due wrong `_load_registry_map`
  argument.

## Observability Verdict

no-evidence-blocker.

The current implementation does not yet produce a working dry-run candidate
proof or an evidence bundle. No Prefect flow runs, live agents, registry writes,
source packet writes, Git mutations, backend/frontend changes, Docker changes,
Playwright runs, provider calls, or product writes were performed by this
review.
