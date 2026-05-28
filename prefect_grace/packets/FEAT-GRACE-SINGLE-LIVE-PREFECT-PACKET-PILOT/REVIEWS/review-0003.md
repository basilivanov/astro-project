# Review 0003 - FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:ac60dc4cb8d9be880a59f7b0b46f0720460606f4dcb8e324d4170fc3bb4719ef
reviewed_commit: 1a02bbb
attempt: rework-after-review-0002
reviewed_at: 2026-05-28

## Verdict

Rework required.

The false-success issue from review-0002 is fixed for `scope_blocked` payloads:
the reader now returns fail-closed instead of inventing `accepted/passed`.
However, the rework introduced a mismatch with the actual managed packet runner
success status and also added a test file outside the packet's allowed write
scope.

No real live agent or Prefect flow run was started during review.

## Blockers

1. Real managed-runner success can be rejected by the status reader.

   The managed packet runner returns `domain_status="passed"` for a successful
   lifecycle (`prefect_grace/platform/managed_packet_runner.py:363`). The pilot's
   final `ok` calculation already treats both `accepted` and `passed` as success
   (`prefect_grace/platform/single_live_prefect_packet_pilot.py:713`). The new
   status reader, though, sets `ok=True` only for
   `domain_status == "accepted" and scope_verdict == "passed"`
   (`prefect_grace/platform/single_live_prefect_packet_pilot.py:393`). A real
   completed managed-runner payload with `domain_status="passed"` and
   `scope_verdict="passed"` therefore returns `ok=False`, which makes the
   caller append `LIVE_PREFECT_STATUS_NOT_OK` and blocks the live proof.

   Reproducer used during review:

   ```python
   from types import SimpleNamespace
   from prefect_grace.platform.single_live_prefect_packet_pilot import create_bounded_prefect_status_reader

   class Client:
       def read_flow_run(self, flow_run_id):
           return SimpleNamespace(
               state_type="COMPLETED",
               state_name="Completed",
               state=SimpleNamespace(data={
                   "domain_status": "passed",
                   "scope_verdict": "passed",
                   "live_agents_started": 1,
                   "changed_files": ["scratch/grace-single-live-prefect/result.txt"],
               }),
           )

   print(create_bounded_prefect_status_reader(Client())(
       flow_run_id="flow-run-passed",
       packet_id="packet",
       timeout_seconds=1,
   ))
   ```

   Actual output has `ok=False` despite explicit passed/passed evidence.

   Required fix: align status-reader success semantics with the managed runner
   and final pilot gate. Either accept `domain_status in {"accepted", "passed"}`
   with `scope_verdict == "passed"`, or change the managed-runner contract and
   all callers consistently. Add a regression for `passed/passed`.

2. Rework added a file outside allowed write scope.

   The packet allows writes to three test files:
   `tests/test_prefect_grace_single_live_prefect_packet_pilot.py`,
   `tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py`, and
   `tests/test_prefect_grace_cli_contracts.py`
   (`EXECUTION_PACKET.md:58`). The rework added
   `tests/test_prefect_grace_bounded_status_reader.py`, which is not in scope.
   `check-scope` reports:

   ```text
   outside_allowed=[{"file_path": "tests/test_prefect_grace_bounded_status_reader.py", "reason": "File is outside allowed write scope"}]
   ```

   Required fix: move the new status-reader tests into an allowed test file, or
   update the execution packet through the normal packet/review process before
   keeping a new file.

3. Rework evidence was not refreshed.

   The evidence directory still only contains `attempt-0001`, and the stored
   `targeted_pytest.txt` artifact still reports `49 passed`, while reviewer
   verification now sees `60 passed`. After the code fixes above, add bounded
   rework evidence under a new attempt directory and validate its manifest.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_bounded_status_reader.py tests/test_prefect_grace_single_live_prefect_packet_pilot.py tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py tests/test_prefect_grace_single_live_packet_pilot.py tests/test_prefect_grace_cli_contracts.py`: `60 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `single_live_prefect_packet_pilot.py`,
  `cli_commands/packet_execution.py`, `cli_commands/parser.py`, and `cli.py`:
  passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation for attempt-0001: `ok=true`, nine artifacts
  validated, nine `unknown_evidence_id` warnings.
- Scope check against `5cf2d39..1a02bbb`: `ok=false` because
  `tests/test_prefect_grace_bounded_status_reader.py` is outside allowed write
  scope.
- Additional reviewer reproducer showed a completed Prefect state with
  managed-runner `passed/passed` payload returns `ok=False`.

## Observability Verdict

unexpected-degradation.

The reader no longer falsely accepts `scope_blocked`, but the live proof can now
falsely reject the managed runner's successful `passed` domain status, and the
commit is outside packet scope. No Prefect flow runs, live agents, registry
writes, source packet writes, Git mutations, backend/frontend changes, Docker
changes, or product writes were performed by this review.
