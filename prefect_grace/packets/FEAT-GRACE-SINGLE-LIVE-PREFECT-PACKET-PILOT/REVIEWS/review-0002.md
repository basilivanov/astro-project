# Review 0002 - FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:ac60dc4cb8d9be880a59f7b0b46f0720460606f4dcb8e324d4170fc3bb4719ef
reviewed_commit: 51354da
attempt: rework-after-review-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The previous missing-reader blocker is only partially fixed. The CLI now passes
a status reader in live mode, and the required missing-deployment / timeout tests
were added. However, the new reader manufactures successful domain/scope evidence
from a Prefect `COMPLETED` state instead of reading the managed-runner result.
That would allow a real run with `scope_blocked`, `runner_error`, or missing
scope evidence to be reported as `accepted` / `passed`.

No real live agent or Prefect flow run was started during review.

## Blockers

1. Bounded status reader returns false success for any completed Prefect run.

   `create_bounded_prefect_status_reader()` records the Prefect state, but on
   `state_type == "COMPLETED"` it returns:

   - `ok=True`
   - `domain_status="accepted"`
   - `scope_verdict="passed"`
   - `live_agents_started=1`
   - `changed_files=[]`

   These are placeholders, not values read from the managed packet runner result
   (`prefect_grace/platform/single_live_prefect_packet_pilot.py:340` and
   `prefect_grace/platform/single_live_prefect_packet_pilot.py:345`). This
   violates the packet objective and bounded polling contract: the pilot must
   prove that the worker consumed the packet and that final domain/scope evidence
   is scratch-only, not infer success from the Prefect terminal state.

   Reproducer used during review:

   ```python
   from types import SimpleNamespace
   from prefect_grace.platform.single_live_prefect_packet_pilot import create_bounded_prefect_status_reader

   class Client:
       def read_flow_run(self, flow_run_id):
           state = SimpleNamespace(data={
               "domain_status": "scope_blocked",
               "scope_verdict": "blocked",
               "changed_files": ["backend/forbidden.py"],
           })
           return SimpleNamespace(state_type="COMPLETED", state_name="Completed", state=state)

   print(create_bounded_prefect_status_reader(Client())(
       flow_run_id="flow-run-001",
       packet_id="packet",
       timeout_seconds=1,
   ))
   ```

   Actual output:

   ```python
   {
       "ok": True,
       "domain_status": "accepted",
       "scope_verdict": "passed",
       "live_agents_started": 1,
       "changed_files": [],
       "poll_events": [...]
   }
   ```

   Required fix: read the flow-run state payload / artifact / state-store record
   produced by the managed packet runner and map only explicit accepted/passed
   evidence to success. If final evidence is missing or not inspectable, return
   fail-closed with a bounded error. Scope-blocked and runner-error domain
   statuses must remain blocked even when the Prefect flow itself is completed.

2. The new status reader itself is not covered by regression tests.

   The added tests cover the pilot with injected `status_reader` functions, but
   they do not exercise `create_bounded_prefect_status_reader()` with fake
   Prefect clients. That leaves the real CLI reader path unprotected. At minimum
   add tests for:

   - completed run with accepted/passed payload -> success;
   - completed run with scope_blocked payload -> fail-closed;
   - completed run with missing payload -> fail-closed;
   - timeout with bounded `poll_events`;
   - failed/cancelled/crashed terminal states -> fail-closed.

   This is the same behavioral surface that the operator command now depends on
   (`prefect_grace/cli_commands/packet_execution.py:556`).

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_single_live_prefect_packet_pilot.py tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py tests/test_prefect_grace_single_live_packet_pilot.py tests/test_prefect_grace_cli_contracts.py`: `51 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `single_live_prefect_packet_pilot.py`,
  `cli_commands/packet_execution.py`, `cli_commands/parser.py`, and `cli.py`:
  passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`, nine artifacts validated, nine
  `unknown_evidence_id` warnings. Attempt evidence is still from attempt-0001
  and the stored pytest artifact still says `49 passed`; rework evidence should
  be refreshed after fixing the blocker.
- Scope check against `5cf2d39..51354da`: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`.
- Additional reviewer reproducer showed completed Prefect state with
  scope-blocked payload incorrectly returns `ok=True`.

## Observability Verdict

unexpected-degradation.

The rework makes the live CLI path reachable, but it can falsely report final
domain/scope success. No Prefect flow runs, live agents, registry writes, source
packet writes, Git mutations, backend/frontend changes, Docker changes, or
product writes were performed by this review.
