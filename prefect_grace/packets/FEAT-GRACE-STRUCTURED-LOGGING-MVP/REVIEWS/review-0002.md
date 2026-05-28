# Review 0002: FEAT-GRACE-STRUCTURED-LOGGING-MVP-W01-LOG-ENVELOPE

status: rework_required
reviewer: codex-reviewer
reviewed_commit: 76fed72 + rework-0001 implementation
source_hash: sha256:1a5d60a9b89d6402ad1b6247499eb3e37dd93e81b602b4ac4b26ab6d3957de60
observability_verdict: unexpected-degradation

## Findings

### Blocker 1: repo-relative trace artifacts resolved via `--artifact-root` still bypass format validation

- file: `prefect_grace/cli_commands/evidence.py:304`
- file: `prefect_grace/platform/evidence_manifest.py:440`
- severity: blocker
- owner: coder

Review-0001 fixed manifest-local sibling paths, but the CLI still calls `validate_evidence_manifest(manifest, contract)` before building/passing the same artifact roots used by `validate_artifact_references()`. As a result, repo-relative trace paths that only resolve through `--artifact-root` pass artifact validation while bypassing `validate_execution_trace_jsonl()`.

Reviewer repro:

```bash
tmp=$(mktemp -d)
mkdir -p "$tmp/root/prefect_grace/packets/PKT/EVIDENCE/attempt-0001/PKT" "$tmp/manifestdir"
printf '{bad-json}\n' > "$tmp/root/prefect_grace/packets/PKT/EVIDENCE/attempt-0001/PKT/execution_trace.jsonl"
# manifestdir/evidence_manifest.json references:
# ["prefect_grace/packets/PKT/EVIDENCE/attempt-0001/PKT/execution_trace.jsonl"]
python3 -m prefect_grace.cli validate-evidence-manifest "$tmp/manifestdir/evidence_manifest.json" \
  --packet "$tmp/EXECUTION_PACKET.md" \
  --artifact-root "$tmp/root" \
  --json
```

Actual result: `ok=true`, `artifact_validation.ok=true`.

Expected result: `ok=false` with `execution_trace_invalid_json`.

Required fix:

- Build artifact roots once in the CLI and pass them into `validate_evidence_manifest(..., artifact_roots=artifact_roots)`.
- Add regression coverage for repo-relative trace paths resolved only through `--artifact-root`.
- If touching `prefect_grace/cli_commands/evidence.py` is needed, update this packet allowed scope in `EXECUTION_PACKET.md` with a narrow rationale and include it in scope validation.
- Keep the review-0001 manifest-local regression passing.

## Checks Run

- Required packet pytest subset -> 36 passed before rework-0002.
- Native submission/scope guard regressions -> 33 passed before rework-0002.
- Managed runner executor/flow regressions -> 12 passed before rework-0002.
- Rework-0001 manifest-local invalid trace repro -> fixed.
- New reviewer repo-relative `--artifact-root` invalid trace repro -> still fails open.

## Notes

The core structured logging implementation still looks directionally sound. The remaining issue is the validation integration path, not trace emission.
