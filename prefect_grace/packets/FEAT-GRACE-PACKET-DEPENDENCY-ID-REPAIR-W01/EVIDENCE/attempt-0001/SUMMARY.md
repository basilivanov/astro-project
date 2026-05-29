# Attempt 0001 Summary

## Scope
- Packet: `FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01-REWORK-RESUME-GATE-ID`
- Target source files:
  - `prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md`
  - `prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md`
- Runtime reconciliation used only scoped `registry-bootstrap-apply` for the two target packet ids.
- No target sidecars were created.
- No Docker, backend, frontend, Playwright, live Prefect, live agents, provider APIs, commit, or push were run.

## Source Repair
- Replaced stale dependency id `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-RESUME-GATE`.
- Replacement dependency id: `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE`.
- Executor Registry hash:
  - before: `sha256:2553a049aab620ebd94ac94d73c89166b3319c783c81d989ff381cd71d2e1743`
  - after: `sha256:3700461e7fb5c11ad9190754c15c07c31c3fb543785b490d22e62b9bb0fa9581`
- Managed Packet Runner hash:
  - before: `sha256:d2b8920f61c7f4e2ea6715cb735209b001777209416e47e0d3a9d4998cbb6d03`
  - after: `sha256:fdda272d31675f6bfcef867494a425fbbe4de6f0a77db9866683081dd2afa313`

## Runtime Registry Reconcile
- Executor Registry preflight planned exactly one accepted target update to `sha256:3700461e7fb5c11ad9190754c15c07c31c3fb543785b490d22e62b9bb0fa9581`.
- Managed Packet Runner preflight planned exactly one accepted target update to `sha256:fdda272d31675f6bfcef867494a425fbbe4de6f0a77db9866683081dd2afa313`.
- Both approved applies reported `apply_count=1`, idempotence `planned_action_counts.noop=1`, `source_mutations=[]`, `writes_outside_runtime_state_root=[]`, and `prefect_runs_created=0`.
- Post-apply packet status reports both targets as `registry_status=accepted` with the new source hashes.

## Final Checks
- Final `sync-packets --dry-run --json`: `ready=["FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01-REWORK-RESUME-GATE-ID"]`, `changed_after_acceptance=[]`, `blocked=[]`, `cascading_blocked=[]`, `registry_updates=0`.
- Final sidecar audit: `canonical=45`, `no_sidecar=52`, `stale_sidecar=0`, `invalid_sidecar=0`, `skipped=2`.
- Self sidecar sync dry-run: `planned_action=noop`, `writes=[]`, `markdown_mutations=[]`.
- Strict repair packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`.
- Scope check: `ok=true`, with changed files limited to the two target packet markdown files and this repair packet directory.
- Stale dependency grep over both target files found no matches.
- `git diff --check` passed for changed packet files.

## Observability Verdict
- Verdict: `clean`
- Evidence is file/CLI based for this bounded packet. No live services were started, and the only runtime mutation was the approved scoped registry reconcile for the two target packet ids.

## Deviations Or Blockers
- None.
