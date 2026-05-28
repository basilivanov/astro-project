# FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY attempt-0002

## Summary
Attempt-0001 applied exactly one explicit missing sidecar for `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`, but post-verification failed because the old sidecar parser treated the legacy H1 title `GRACE Agent API Failure Classification MVP` as markdown packet id `GRACE`.

Attempt-0002 re-ran verification after accepted parser prerequisite `FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE-W01-HEADING-ID-GUARD` and did not re-run sidecar migration apply. The existing target sidecar is now canonical.

## Post-Parser Audit
- Command: `audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- ok: true
- canonical: 10
- no_sidecar: 63
- stale_sidecar: 0
- invalid_sidecar: 0
- skipped: 2
- target sidecar: canonical
- writes/source_mutations: []
- prefect_runs_created/live_agents_started: 0/0

## Post-Parser Plan
- Command: `plan-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --json --limit 100`
- ok: true
- plan_count: 63
- risk_counts: `accepted_source_hash_change=63`
- target packet is not in remaining plan items.
- no invalid finding exists for the target packet.

## Sync Packets
- Command: `sync-packets --project prefect_grace/project.yaml --dry-run --json`
- ok: true
- changed_after_acceptance: [`FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`]
- errors: []
- no `GRACE` packet-id mismatch occurred.

## Target Runtime Status
- Command: `packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER --json`
- registry_status: accepted
- packet status: ready
- registry source_hash: `sha256:760c9c28f6576401349adc7e85aa42394902acbd7c2fe7beda9d1ba358e58ec6`
- source hash remains unreconciled by this packet as expected.

## Packet Local Verification
- Self-sidecar sync dry-run: noop.
- Strict packet validation: pass.
- Evidence manifest validation: see `validate_evidence_manifest.json`.
- Scope check: see `scope_check.json`.
- `git diff --check`: see `diff_check.txt`.

## Observability Verdict
degraded-but-expected. Parser-era sidecar verification is clean (`invalid_sidecar=0`, `stale_sidecar=0`), and the only remaining degradation is the expected accepted-packet source hash mismatch for the target packet pending a later reconcile packet.
