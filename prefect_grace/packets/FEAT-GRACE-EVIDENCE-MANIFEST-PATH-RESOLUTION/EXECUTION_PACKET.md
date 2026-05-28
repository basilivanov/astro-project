# Execution Packet: FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION-W01-MANIFEST-RELATIVE-ARTIFACTS

## Objective

Make `validate-evidence-manifest` accept evidence artifact paths that are
relative to the manifest directory, while preserving the existing repo-relative,
artifact-root-relative, and absolute-under-root behavior.

The nightly dry-run controller review exposed a recurring convention mismatch:
agents naturally write evidence manifests like:

```json
{
  "artifact_paths": ["targeted_pytest.txt"]
}
```

when the artifact lives beside `evidence_manifest.json` in
`EVIDENCE/attempt-0001/`. The current validator only resolves relative paths
against `--artifact-root`, so the same manifest fails unless every artifact path
is expanded to a full repo-relative path. This packet should make the validator
support both forms without weakening path containment.

This is evidence validation infrastructure only. It must not change packet
execution, runtime registry status inference, live runs, or product behavior.

## Slice

- slice_id: `SLICE-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION`
- slice_slug: `grace-evidence-manifest-path-resolution`
- feature_id: `FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION`
- packet_id: `FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION-W01-MANIFEST-RELATIVE-ARTIFACTS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY, FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/evidence_contract.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_artifact_validator.py`
- `/opt/astro-project/tests/test_prefect_grace_evidence_manifest.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/EVIDENCE/attempt-0001/evidence_manifest.json`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/REVIEWS/review-0001.md`

## Impacted Modules

- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-ARTIFACT-VALIDATOR`
- `M-GRACE-EVIDENCE-CLI`
- `M-GRACE-PACKET-EVIDENCE-LAYOUT`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_artifact_validator.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_evidence_manifest_paths.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_evidence_manifest.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Existing absolute-under-artifact-root validation remains accepted.
- Existing artifact-root-relative validation remains accepted.
- Absolute paths outside allowed roots remain rejected.
- Relative paths that traverse outside their allowed root remain rejected.
- Non-collected evidence items remain skipped by artifact validation.
- `validate-evidence-manifest` JSON envelope keeps `result == data`.
- Unknown evidence IDs remain non-blocking warnings when the evidence contract does not define them.
- No source packet, runtime registry, worktree, live Prefect, agent, backend, frontend, Docker, Playwright, provider API, or credentialed service is touched.

## Recommended Role Assignment

- coder: `Codex medium`; this is a small validation compatibility fix.
- verifier: `Codex medium`; must cover CLI and validator API regressions.
- reviewer: `Codex high`; reviewer should focus on path traversal and
  containment, not just green happy-path tests.
- rework policy: light resume is acceptable for tests, help text, or evidence
  formatting; fresh session for path traversal or root containment bugs.

## Required Design Decisions

### 1. Support Both Path Conventions

The validator must accept both of these when the artifact exists:

```json
{
  "artifact_paths": ["targeted_pytest.txt"]
}
```

and:

```json
{
  "artifact_paths": [
    "prefect_grace/packets/FEAT-X/EVIDENCE/attempt-0001/targeted_pytest.txt"
  ]
}
```

The first form resolves relative to the directory containing
`evidence_manifest.json`. The second form resolves relative to the explicit
artifact root, typically `/opt/astro-project`.

### 2. CLI Should Own Manifest-Relative Context

`prefect_grace.platform.artifact_validator.validate_artifact_references(...)`
currently receives a manifest model and allowed roots. It does not know the
manifest file path.

Implementation may either:

- add a backward-compatible optional `manifest_dir` or `extra_relative_roots`
  parameter to the validator API; or
- keep the validator API unchanged and have `_cmd_validate_evidence_manifest`
  pass `args.manifest_path.parent` as an additional allowed relative root.

The chosen design must be covered by tests and must not break existing callers
such as verifier/reviewer handoff.

### 3. Explicit Artifact Root Still Matters

When `--artifact-root /opt/astro-project` is supplied, repo-relative artifact
paths must continue to work.

Manifest-relative paths must be accepted only when the resolved file stays
inside the manifest directory or inside an allowed artifact root. Do not allow
`../..` traversal to escape into unrelated filesystem areas.

### 4. Fail Closed On Traversal

These must remain invalid:

```json
{
  "artifact_paths": ["../../../../etc/passwd"]
}
```

and absolute paths outside allowed roots.

Validation should report the original artifact string in
`missing_artifacts`/validated references so operators can fix the manifest.

### 5. No Runtime Behavior Change

This packet must not change:

- bootstrap acceptance inference;
- registry apply behavior;
- nightly dry-run planning;
- submit/execute behavior;
- evidence manifest schema fields;
- source packet format.

## Implementation Requirements

1. Add regression tests showing `validate-evidence-manifest` accepts short artifact names beside `evidence_manifest.json`.
2. Add regression tests showing repo-relative artifact paths still validate with `--artifact-root /opt/astro-project`.
3. Add regression tests showing traversal from manifest directory is rejected.
4. Add regression tests showing absolute paths outside allowed roots remain rejected.
5. Keep existing artifact validator tests passing.
6. Update CLI help or comments only if useful; do not add noisy operator output.
7. Add bounded evidence under `EVIDENCE/attempt-0001/`.

## Acceptance Criteria

- `validate-evidence-manifest <manifest> --packet <packet> --artifact-root /opt/astro-project --json` accepts manifest-local `artifact_paths` such as `targeted_pytest.txt`.
- The same command accepts repo-relative artifact paths.
- Path traversal from the manifest directory is rejected.
- Absolute paths outside allowed roots are rejected.
- Existing `validate_artifact_references(...)` tests still pass.
- CLI JSON envelope remains stable and `result == data`.
- The fix does not mutate existing packet evidence outside this packet.
- No live agents, live Prefect runs, runtime registry writes, source packet rewrites, backend, frontend, Docker, Playwright, provider APIs, or credentials are used.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_artifact_validator.py \
  tests/test_prefect_grace_cli_evidence_manifest_paths.py \
  tests/test_prefect_grace_evidence_manifest.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/artifact_validator.py \
  prefect_grace/cli_commands/evidence.py \
  prefect_grace/cli_commands/parser.py
```

Run targeted GRACE lint:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/artifact_validator.py \
  prefect_grace/cli_commands/evidence.py \
  prefect_grace/cli_commands/parser.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI proof against a temp manifest with short sibling artifact paths:

```bash
python3 -m prefect_grace.cli validate-evidence-manifest \
  /tmp/grace-evidence-path-resolution/EVIDENCE/attempt-0001/evidence_manifest.json \
  --packet /tmp/grace-evidence-path-resolution/EXECUTION_PACKET.md \
  --artifact-root /tmp/grace-evidence-path-resolution \
  --json
```

Run CLI proof against traversal/outside-root cases and confirm `ok=false`.

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, live
agents, provider APIs, or credentialed services for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- CLI proof for manifest-relative short artifact paths.
- CLI proof for repo-relative artifact paths.
- CLI proof for traversal rejection.
- CLI proof for absolute outside-root rejection.
- Confirmation that existing nightly evidence would validate with short sibling artifact paths.
- Confirmation that no source packet evidence outside this packet was rewritten.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- Supporting manifest-relative paths requires weakening absolute path containment.
- Supporting manifest-relative paths requires rewriting existing evidence files.
- Existing repo-relative or absolute-under-root behavior breaks.
- Traversal paths can validate.
- The evidence manifest schema would need a breaking change.
- Bootstrap acceptance inference or runtime registry behavior would need changes.
- Product backend/frontend files need changes.
- Evidence cannot be kept bounded.

## Reviewer Gate

Reviewer must reject this packet if:

- short sibling artifact paths still fail through `validate-evidence-manifest`;
- repo-relative artifact paths fail when `--artifact-root` is supplied;
- `../` traversal can escape the manifest directory or artifact root;
- absolute paths outside allowed roots validate;
- existing artifact validator tests regress;
- CLI JSON envelope compatibility breaks;
- existing packet evidence outside this packet is rewritten;
- live agents, live Prefect runs, registry writes, worktrees, Docker, backend,
  frontend, Playwright, provider APIs, or credentials are used.
