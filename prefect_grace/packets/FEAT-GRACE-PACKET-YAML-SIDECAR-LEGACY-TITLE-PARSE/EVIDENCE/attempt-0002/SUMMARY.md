# FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE-W01-HEADING-ID-GUARD

## Summary
Reworked the H1 packet id guard after review. `_looks_like_packet_id()` no longer accepts any `FEAT-*` token unconditionally. H1-derived values now become markdown packet ids only when they contain a real wave segment, including terminal wave segments. Explicit `packet_id` metadata remains authoritative even when it has no wave segment.

## Regression Coverage
- Descriptive H1 `GRACE Agent API Failure Classification MVP` with explicit matching sidecar parses successfully.
- Feature-like H1 `FEAT-GRACE-PREFECT-LIVE-PILOT-PAYLOAD-RETRIEVAL` with explicit `...-W01-PAYLOAD` sidecar parses successfully and uses the explicit id.
- Explicit markdown/sidecar packet id mismatch still fails.
- H1 packet id with wave segment still parses when no explicit packet id exists.

## Verification Verdict
clean for parser tests, compile, lint, strict packet validation, evidence manifest validation, sidecar audit, scope check, and whitespace diff checks.

## Observability Verdict
degraded-but-expected for `sync-packets --dry-run`: it succeeds without a legacy H1 mismatch and still reports the pre-existing dirty AGENT API sidecar as `changed_after_acceptance`, as expected.
