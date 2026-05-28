# Evidence - attempt-0002

Packet: FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-MANAGED-PREFECT-SCRATCH-RUN

Rework after review-0003.

Summary:

- Fixed status reader to accept both "accepted" and "passed" domain_status (aligns with managed_packet_runner.py).
- Moved status reader tests from out-of-scope file into allowed test file.
- Added regression test for passed/passed payload.
- Status reader now correctly reads real payload from flow run state.
- Fails closed for scope_blocked, missing payload, incomplete evidence, and non-success terminal states.
- Dry-run default plans exactly one synthetic scratch packet and creates zero Prefect runs / zero live agents.
- Live mode requires `--no-dry-run`, `--execute-agent`, `--i-understand-live-agent`, and `GRACE_LIVE_PREFECT_PACKET_OPT_IN=single-live-prefect`.
- Injected live proof covers exactly one managed Prefect run, one agent launch, accepted/passed domain status, and scratch-only scope.
- Test coverage: 61 tests passed (7 pilot integration + 10 status reader unit + 44 supporting).
- Real live agent and real managed Prefect flow execution were not run.

Observability verdict: degraded-but-expected.
