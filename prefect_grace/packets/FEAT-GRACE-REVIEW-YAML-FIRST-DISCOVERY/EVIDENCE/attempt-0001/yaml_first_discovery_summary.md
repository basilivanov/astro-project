# YAML-First Review Discovery Evidence

## Summary

- `latest_review(layout)` now discovers `.yaml`, `.yml`, and `.md` review artifacts.
- Latest review selection uses the numeric `review-000N` stem.
- Same numeric review preference is `.yaml`, then `.yml`, then `.md`.
- Merge steward, git mutation gate, and nightly preflight review checks now use the shared layout helper.
- Context bundle audit mode includes YAML and YML review artifacts.

## Verification Results

- Targeted pytest: `80 passed in 2.57s`
- Compileall: passed
- `grace_lint` per touched platform module: passed
- `validate-packet --strict --json`: passed
- `validate-evidence-manifest --json`: passed with existing empty-contract warning `unknown_evidence_id`
- `git diff --check`: passed
- Post-test observability verdict: `clean` for local deterministic unit/contract flow; no runtime trace, digest, replay, backend, frontend, Docker, Prefect, or live-agent evidence was expected for this packet profile.
