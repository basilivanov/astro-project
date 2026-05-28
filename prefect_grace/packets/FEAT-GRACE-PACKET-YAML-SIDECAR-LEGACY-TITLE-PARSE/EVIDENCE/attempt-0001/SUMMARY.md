# FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE-W01-HEADING-ID-GUARD

## Summary
Implemented a narrow H1 packet id guard in `prefect_grace/platform/packet_parser.py`. H1 values after `Execution Packet:` now seed markdown packet ids only when they look like controller packet ids. Descriptive legacy titles remain titles only, so explicit `packet_id` metadata remains authoritative for strict packets and YAML sidecar mismatch detection.

## Verification Verdict
clean for parser tests, compile, lint, strict packet validation, evidence manifest validation, sidecar audit, and whitespace diff checks.

## Observability Verdict
degraded-but-expected for `sync-packets --dry-run`: the command no longer fails on the legacy `GRACE` mismatch, and it reports the pre-existing dirty AGENT API packet sidecar as `changed_after_acceptance`, which was expected by the task.

## Scope
Only the parser, focused parser tests, and this packet's artifacts were changed. Existing dirty/untracked registry, ASTRO, missing-sidecar, and AGENT API sidecar artifacts were not modified.
