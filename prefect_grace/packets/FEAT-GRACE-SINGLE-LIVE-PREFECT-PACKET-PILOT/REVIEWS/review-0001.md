# Review 0001 - FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:ac60dc4cb8d9be880a59f7b0b46f0720460606f4dcb8e324d4170fc3bb4719ef
reviewed_commit: 8d40159
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The static gates and injected tests are green, but the operator CLI path cannot
yet prove the packet's live Prefect contract. The packet asks for a real managed
Prefect submission whose worker consumes the packet and returns bounded final
domain/scope evidence. The current CLI can submit a run, but it never wires a
real final-status reader, so a manually approved live proof through the command
would end in `LIVE_PREFECT_FINAL_EVIDENCE_PENDING` /
`LIVE_PREFECT_STATUS_NOT_OK`.

No real live agent or Prefect flow run was started during review.

## Blockers

1. Real CLI path cannot complete the live worker proof.

   Packet lines 90-102 require the real path to go through Prefect and, when
   waiting, use bounded polling with a timeout, bounded events, and final status
   summary. Lines 109-113 require worker timeout, accepted, scope-blocked, and
   manually approved live proof coverage. In the implementation,
   `_status_reader_result()` returns `LIVE_PREFECT_FINAL_EVIDENCE_PENDING`
   whenever no reader is injected (`prefect_grace/platform/single_live_prefect_packet_pilot.py:243`).
   The real non-dry-run branch always relies on that result after submission
   (`prefect_grace/platform/single_live_prefect_packet_pilot.py:423` and
   `prefect_grace/platform/single_live_prefect_packet_pilot.py:456`), while the
   CLI call does not pass any status reader
   (`prefect_grace/cli_commands/packet_execution.py:555`). This means the
   operator command cannot produce the required final `domain_status`,
   `scope_verdict`, bounded `poll_events`, or successful `ok=true` live proof.

   Required fix: wire a real bounded status reader/poller into the CLI path, or
   explicitly split the real final-status proof into a later packet and narrow
   this packet's contract to injected-only evidence. If kept in this packet, the
   CLI must report timeout, event cap, final domain/scope summary, and avoid
   unbounded log streaming.

2. Required failure-mode coverage is missing.

   The packet requires coverage for missing deployment and worker timeout
   (`EXECUTION_PACKET.md:109`). The current tests cover dry-run, missing opt-in,
   injected accepted, injected scope-blocked, and multiple ready packets, but
   there is no regression for a submitter/deployment-not-found failure and no
   regression for a status-reader timeout
   (`tests/test_prefect_grace_single_live_prefect_packet_pilot.py:24`). Without
   those tests, the runner can regress exactly in the two cases that matter
   before the first real live execution.

   Required fix: add an injected missing-deployment test that proves zero flow
   runs / zero agents and a bounded error, plus an injected worker-timeout test
   that proves one submitted flow run, fail-closed `ok=false`, bounded
   `poll_events`, and no writes outside scratch/temp roots.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_single_live_prefect_packet_pilot.py tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py tests/test_prefect_grace_single_live_packet_pilot.py tests/test_prefect_grace_cli_contracts.py`: `49 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `single_live_prefect_packet_pilot.py`,
  `cli_commands/packet_execution.py`, `cli_commands/parser.py`, and `cli.py`:
  passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`, nine artifacts validated. The
  manifest still reports `unknown_evidence_id` warnings because the packet lists
  prose evidence names rather than strict IDs; this is not the blocker.
- Scope check against `5cf2d39..8d40159`: `ok=true`, `outside_allowed=[]`,
  `frozen_violations=[]`.

## Observability Verdict

degraded-but-expected.

The existing evidence is acceptable for dry-run and injected live behavior, but
it does not prove a real worker-consumed Prefect run. No Prefect flow runs, live
agents, registry writes, source packet writes, Git mutations, backend/frontend
changes, Docker changes, or product writes were performed by this review.
