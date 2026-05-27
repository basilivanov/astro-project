# Review 0001 — FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP

status: rework_required
reviewer: codex
source_hash: sha256:c7d8cb8ed4430a12780346ca851bbc985b8d760f6420c192fcea7a363ca3a2b5
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

The main implementation is close and the packet verification commands pass, but
there is a critical artifact validation bug: verifier evidence can currently
claim absolute paths or path traversal outside allowed artifact roots and still
be accepted.

This violates the packet contract and the Evidence Contracts MVP rule that LLM
artifact references are not trusted until deterministically validated.

## Blocking Issues

### 1. Artifact validation allows absolute paths outside allowed roots

Observed with a direct negative check against
`prefect_grace.platform.verifier_reviewer_handoff.validate_verifier_evidence`:

```python
ok, errors = validate_verifier_evidence(
    {
        "packet_id": "P",
        "generated_by": "verifier",
        "requirement_results": [
            {
                "id": "EV-ABS",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["/etc/passwd"],
                "summary": "bad abs path",
            }
        ],
    },
    packet_dir,
    [packet_dir],
)
```

Actual result:

```text
{'ok': True, 'errors': []}
```

Expected result:

```text
ok == False
error indicates artifact path outside allowed roots
```

Root cause: the current implementation checks `root / artifact_path`. In Python,
`Path(root) / Path('/absolute/path')` resolves to the absolute path and ignores
`root`.

### 2. Artifact validation allows `..` traversal outside allowed roots

Observed negative check:

```python
artifact_paths = ["../outside.txt"]
```

When the outside file exists, validation returns:

```text
{'ok': True, 'errors': []}
```

Expected result:

```text
ok == False
error indicates path traversal outside allowed roots
```

Required behavior:

- resolve each claimed artifact path;
- accept it only if the resolved path is equal to or under one allowed root;
- reject absolute paths outside allowed roots;
- reject relative traversal outside allowed roots;
- preserve support for valid relative paths under `packet_dir` or `worktree_path`.

Prefer reusing `prefect_grace.platform.artifact_validator` instead of duplicating
path-safety logic inside `verifier_reviewer_handoff.py`.

### 3. Evidence manifest still contains out-of-scope transient diff

`EVIDENCE/attempt-0001/evidence_manifest.md` currently reports:

```text
automation/cli_health.yaml | 2 +-
```

`automation/cli_health.yaml` is not in `Allowed Write Scope`. It appears to be
transient CLI health noise, but it must not appear in acceptance evidence.

### 4. Evidence CLI smoke is weaker than packet verification contract

The packet verification requires an offline `run-handoff` smoke with fake
verifier/reviewer output files. Current evidence records only:

```bash
python3 -m prefect_grace.cli run-handoff --help
```

That is useful, but not enough for acceptance. Evidence must include a real
fake/offline `run-handoff ... --json` execution that does not launch live agents.

## Confirmed Passing Checks

The exact verification commands from the packet passed before the negative
artifact path checks above.

### Targeted Tests

```bash
pytest -q \
  tests/test_prefect_grace_verifier_reviewer_handoff.py \
  tests/test_prefect_grace_verifier_reviewer_handoff_flow.py \
  tests/test_prefect_grace_handoff_artifacts.py \
  tests/test_prefect_grace_cli_handoff.py \
  tests/test_prefect_grace_cli_contracts.py
```

Result:

```text
46 passed in 3.19s
```

### Regression Tests

```bash
pytest -q \
  tests/test_prefect_grace_evidence_contract.py \
  tests/test_prefect_grace_evidence_manifest.py \
  tests/test_prefect_grace_artifact_validator.py \
  tests/test_prefect_grace_packet_artifact_layout.py \
  tests/test_prefect_grace_managed_packet_runner.py
```

Result:

```text
67 passed in 0.40s
```

### Static Checks

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/verifier_reviewer_handoff.py
python3 scripts/grace_lint.py prefect_grace/flows/verifier_reviewer_handoff_flow.py
python3 scripts/grace_lint.py prefect_grace/tasks/handoff_artifacts.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Result:

```text
PASS
```

## Required Rework

1. Fix artifact path validation in `verifier_reviewer_handoff.py` so absolute
   and traversal paths outside allowed roots fail closed.
2. Add regression tests for:
   - absolute path outside allowed roots;
   - `..` traversal outside allowed roots;
   - valid relative artifact under packet dir still accepted;
   - valid artifact under worktree path still accepted.
3. Regenerate `EVIDENCE/attempt-0001/evidence_manifest.md` after reverting
   transient `automation/cli_health.yaml`.
4. Include a real offline CLI smoke command with fake verifier/reviewer output
   files, not only `run-handoff --help`.
5. Keep frozen scope untouched:
   - `scripts/grace_lint.py`;
   - `codex_launcher.py`;
   - `review_router.py`;
   - `state_store.py`;
   - feature pipeline and product backend/frontend files.

## Acceptance Condition

Next review can accept if:

- exact verification remains green;
- negative artifact path checks fail closed;
- evidence manifest is limited to allowed scope;
- offline `run-handoff ... --json` smoke is included in evidence;
- no live agents, Prefect server, registry acceptance, merge, push, or rework
  packet creation occurs during tests.
