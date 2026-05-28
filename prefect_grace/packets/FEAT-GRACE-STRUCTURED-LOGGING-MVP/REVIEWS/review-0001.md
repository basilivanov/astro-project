# Review 0001: FEAT-GRACE-STRUCTURED-LOGGING-MVP-W01-LOG-ENVELOPE

status: rework_required
reviewer: codex-reviewer
reviewed_commit: 76fed72 + uncommitted implementation
source_hash: sha256:1a5d60a9b89d6402ad1b6247499eb3e37dd93e81b602b4ac4b26ab6d3957de60
observability_verdict: unexpected-degradation

## Findings

### Blocker 1: manifest-local execution traces are not format-validated

- file: `prefect_grace/platform/evidence_manifest.py:391`
- severity: blocker
- owner: coder

`validate_evidence_manifest()` only calls `validate_execution_trace_jsonl()` when `Path(artifact_path).exists()` is true relative to the current working directory. The CLI already resolves collected artifacts against `args.manifest_path.parent` and `--artifact-root` in `artifact_validator`, so normal manifest-local paths such as `execution_trace.jsonl` can exist and pass artifact validation while completely bypassing trace JSONL validation.

Reviewer repro:

```bash
tmp=$(mktemp -d)
cp prefect_grace/packets/FEAT-GRACE-STRUCTURED-LOGGING-MVP/EXECUTION_PACKET.md "$tmp/EXECUTION_PACKET.md"
printf '{bad-json}\n' > "$tmp/execution_trace.jsonl"
# evidence_manifest.json references ["execution_trace.jsonl"]
python3 -m prefect_grace.cli validate-evidence-manifest "$tmp/evidence_manifest.json" \
  --packet "$tmp/EXECUTION_PACKET.md" \
  --artifact-root "$tmp" \
  --json
```

Actual result: `ok=true`, `artifact_validation.ok=true`.

Expected result: `ok=false` with `execution_trace_invalid_json` or equivalent trace validation error.

This violates the packet acceptance criteria: “Evidence manifest validates trace files” and the escalation trigger “Evidence manifest rejects valid trace files” in the inverse direction: malformed trace files are accepted.

Required fix:

- Resolve trace artifacts through the same allowed roots used by artifact validation, including manifest-local paths.
- Add a regression test proving invalid manifest-local `execution_trace.jsonl` fails validation.
- Keep traversal/absolute outside-root protections intact.

## Checks Run

- `pytest -q tests/test_prefect_grace_structured_logger.py tests/test_prefect_grace_trace_context.py tests/test_prefect_grace_log_collector.py tests/test_prefect_grace_managed_packet_runner.py tests/test_prefect_grace_single_astro_packet_pilot.py` -> 36 passed.
- `pytest -q tests/test_prefect_grace_prefect_native_submission.py tests/test_prefect_grace_scope_guard.py` -> 33 passed.
- `pytest -q tests/test_prefect_grace_managed_packet_runner_executor_registry.py tests/test_prefect_grace_managed_packet_runner_flow.py` -> 12 passed.
- `python3 -m compileall -q prefect_grace/platform` -> pass.
- Targeted `grace_lint.py` per touched platform file -> pass.
- `validate-packet --strict --json` -> ok=true.
- `check-scope --changed-files-file ... --json` -> ok=true.
- `validate-evidence-manifest ... --json` on attempt-0001 -> ok=true.
- `git diff --check` -> pass.

## Notes

Core logger, trace context, collector, and runner/pilot trace emission look directionally correct. The rework should stay focused on trace artifact validation and updated evidence.
