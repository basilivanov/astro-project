# Review 0004 - FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT

status: rework_required
reviewer: codex
source_hash: sha256:ac60dc4cb8d9be880a59f7b0b46f0720460606f4dcb8e324d4170fc3bb4719ef
reviewed_commit: ea3cb95
attempt: rework-after-review-0003
reviewed_at: 2026-05-28

## Verdict

Rework required for evidence only.

The code blockers from review-0003 are fixed. The status reader now accepts both
`accepted/passed` and `passed/passed`, and the status-reader tests were moved
back into the packet's allowed test file. Scope check is clean.

The packet still cannot be accepted because the evidence bundle was not
refreshed after the rework.

No real live agent or Prefect flow run was started during review.

## Blockers

1. Rework evidence is stale and incomplete.

   The packet evidence directory still contains only `EVIDENCE/attempt-0001`.
   Its stored `targeted_pytest.txt` reports `49 passed`, but the current review
   run for the reworked code reports `61 passed`. There is no new bounded
   attempt directory proving:

   - the `passed/passed` regression is covered;
   - scope check is now clean after deleting
     `tests/test_prefect_grace_bounded_status_reader.py`;
   - the current compile/lint/packet validation/evidence validation outputs
     match commit `ea3cb95`.

   Required fix: add a new evidence attempt for this rework, refresh the relevant
   artifacts, and validate its manifest. No code change is required for this
   blocker unless evidence generation exposes a new issue.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_single_live_prefect_packet_pilot.py tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py tests/test_prefect_grace_single_live_packet_pilot.py tests/test_prefect_grace_cli_contracts.py`: `61 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `single_live_prefect_packet_pilot.py`,
  `cli_commands/packet_execution.py`, `cli_commands/parser.py`, and `cli.py`:
  passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation for stale attempt-0001: `ok=true`, nine
  artifacts validated, nine `unknown_evidence_id` warnings.
- Scope check against `5cf2d39..ea3cb95`: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`.
- Reviewer reproducer for completed Prefect state with managed-runner
  `passed/passed` payload now returns `ok=True`.

## Observability Verdict

no-evidence-blocker.

Runtime behavior reviewed cleanly for the bounded static/injected profile, but
the packet lacks current rework evidence. No Prefect flow runs, live agents,
registry writes, source packet writes, Git mutations, backend/frontend changes,
Docker changes, or product writes were performed by this review.
