# Execution Packet: FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE-W01-STRICT-PACKET-ID

## Objective

Add a fail-closed identity gate to GRACE evidence manifest validation so a
manifest cannot validate successfully when its `packet_id` is missing,
`UNKNOWN`, or different from the parsed packet contract packet id.

Also preserve backward compatibility for legacy verifier handoff manifests that
use `requirement_results` as the evidence list, while keeping canonical
`evidence` output from `to_dict()`.

## Slice

- slice_id: `SLICE-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE`
- slice_slug: `grace-evidence-manifest-identity-gate`
- feature_id: `FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE`
- packet_id: `FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE-W01-STRICT-PACKET-ID`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/prefect_grace/platform/evidence_contract.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/tests/test_prefect_grace_evidence_manifest.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_evidence_manifest_paths.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_evidence_manifest_identity.py`

## Impacted Modules

- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-CLI`
- `M-GRACE-EVIDENCE-VALIDATION`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/tests/test_prefect_grace_evidence_manifest.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_evidence_manifest_paths.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_evidence_manifest_identity.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/executor_history.yaml`
- `/opt/astro-project/prefect_grace/packet_registry.yaml`
- `/opt/astro-project/prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**`
- `/opt/astro-project/prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**`
- `/opt/astro-project/prefect_grace/platform/** outside allowed scope`
- `/opt/astro-project/prefect_grace/cli_commands/** outside allowed scope`
- `/opt/astro-project/tests/** outside allowed scope`
- `/var/lib/**`

## Must Preserve

- Artifact reference validation continues to resolve manifest-local paths.
- Unknown evidence ids remain warnings when packet identity is valid.
- Canonical manifest serialization keeps the `evidence` field.
- CLI JSON envelope keeps `result == data`.
- Bootstrap, registry inference, backend, frontend, and runtime registry state are not changed.

## Required Design Decisions

### 1. Identity Gate Location

Place identity validation in `validate_evidence_manifest()` so platform callers
and CLI callers share the same fail-closed behavior.

### 2. Identity Rules

Reject manifests when:

- `packet_id` is missing or blank;
- `packet_id` is `UNKNOWN`;
- `packet_id` does not match the parsed packet contract packet id.

Use explicit error codes:

- `manifest_packet_id_missing`;
- `manifest_packet_id_unknown`;
- `manifest_packet_id_mismatch`.

### 3. Legacy Evidence Alias

`EvidenceManifest.from_dict()` should treat `requirement_results` as the
evidence list only when canonical `evidence` is absent. If both fields are
present, `evidence` wins.

## Implementation Requirements

1. Update evidence manifest parser alias handling.
2. Add packet identity validation to the shared manifest validator.
3. Add platform tests for matching, missing, UNKNOWN, and mismatched packet id.
4. Add parser tests for `requirement_results` alias and canonical precedence.
5. Add CLI tests proving UNKNOWN/mismatch exit nonzero with `ok=false`, and a
   matching legacy alias manifest exits zero when artifacts are valid.

## Acceptance Criteria

- Matching manifest and contract packet id validates.
- Missing, `UNKNOWN`, and mismatched manifest packet ids fail validation.
- Legacy `requirement_results` manifests no longer produce an empty evidence list.
- CLI `validate-evidence-manifest` exits `1` and returns JSON `ok=false` for bad packet identity.
- Manifest-local artifact validation remains green.

## Verification

Run:

```bash
python3 -m pytest -q tests/test_prefect_grace_evidence_manifest.py tests/test_prefect_grace_cli_evidence_manifest_paths.py tests/test_prefect_grace_cli_evidence_manifest_identity.py
python3 -m compileall -q prefect_grace/platform/evidence_manifest.py prefect_grace/cli_commands/evidence.py
python3 scripts/grace_lint.py prefect_grace/platform/evidence_manifest.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/evidence.py
python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE/EXECUTION_PACKET.md --strict --json
python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-IDENTITY-GATE/EXECUTION_PACKET.md --artifact-root /opt/astro-project --json
git diff --check
```

## Expected Evidence

- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Strict packet validation output.
- Evidence manifest validation output.
- Observability verdict with post-test evidence review.

## Escalation Triggers

- A manifest with missing, `UNKNOWN`, or mismatched packet id validates.
- A legacy `requirement_results` manifest silently validates with zero evidence.
- Manifest-local artifact paths regress.
- Registry, bootstrap, backend, frontend, or runtime state changes appear.
