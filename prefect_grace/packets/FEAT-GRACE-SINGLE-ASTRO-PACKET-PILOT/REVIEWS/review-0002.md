# Review 0002 - FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:3ceefd97e17f636c6c8b49326fc885c9aa6d319917dd94c1758fccc4a1ef6ed9
reviewed_commit: 837f3d4 + uncommitted rework
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The review-0001 wiring blockers are fixed: the CLI command exists, the real
dry-run no longer fails with `REGISTRY_LOAD_FAILED`, managed submission uses the
existing `submit_ready_packets_to_prefect()` API, dataclass records are handled,
and the required behavioral tests/evidence bundle were added.

The remaining blocker is output bounding. The real project dry-run succeeds but
prints the full runtime registry in the operator JSON envelope, producing a
9491-line response for a one-packet dry-run. That violates this packet's
bounded evidence/output contract and is exactly the kind of output the
orchestrator must avoid before nightly or live training runs.

No real live agent or Prefect flow run was started during review.

## Blockers

1. Operator JSON output is not bounded on the real registry.

   `SingleAstroPacketPilotResult` exposes full `registry_before` and
   `registry_after` maps (`prefect_grace/platform/single_astro_packet_pilot.py:61`
   and `:62`). The implementation fills `registry_before` from the entire
   project registry (`prefect_grace/platform/single_astro_packet_pilot.py:406`)
   and returns full `registry_before`/`registry_after` in `to_dict()`
   (`prefect_grace/platform/single_astro_packet_pilot.py:650` and `:651`).
   The CLI then emits the full result payload
   (`prefect_grace/cli_commands/packet_execution.py:650` through `:659`).

   A direct dry-run against `prefect_grace/project.yaml` now returns `ok=true`
   and selects exactly one packet, but the JSON output is 9491 lines because it
   includes every registry entry and parsed packet metadata:

   ```text
   command: run-single-astro-packet-pilot
   ok: true
   selected_packet_id: FEAT-ASTRO-CACHE-MANAGER-W01-LRU-CACHE
   prefect_runs_created: 0
   live_agents_started: 0
   output_lines: 9491
   ```

   This contradicts `EXECUTION_PACKET.md:84` (`Evidence is bounded`) and trips
   the escalation trigger at `EXECUTION_PACKET.md:157` (`Output includes
   unbounded logs or secrets`). The issue scales with registry size and will get
   worse as more Astro packets are added.

   Required fix: replace the full registry maps in the public result/CLI JSON
   with bounded summaries. Keep enough evidence to audit the run, for example
   counts by status, selected packet metadata, selected packet source hash,
   rejection/error summaries, and changed/runtime counters. Do not emit all
   registry records by default. Preserve the `result == data` JSON envelope
   contract and add a regression that fails if a real-project dry-run output
   grows past a bounded threshold.

## Verification Reviewed

- Packet-specified pytest profile:
  `63 passed in 13.69s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint:
  `single_astro_packet_pilot.py`, `packet_execution.py`, and `parser.py` passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`; artifact validation passed, with
  non-blocking `unknown_evidence_id` warnings from the current evidence
  contract parser.
- Scope check against the packet allowed scope: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`.
- Direct real CLI dry-run:
  `ok=true`, selected `FEAT-ASTRO-CACHE-MANAGER-W01-LRU-CACHE`,
  `prefect_runs_created=0`, `live_agents_started=0`, but output was 9491 lines.

## Observability Verdict

unexpected-degradation.

The runtime behavior is functionally closer to the intended pilot, but the
operator/evidence surface is not bounded. No Prefect flow runs, live agents,
registry apply, source packet mutation, Git commit/push/merge, backend/frontend
service start, Docker, Playwright, or provider calls were performed by this
review.
