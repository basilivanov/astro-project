# Review 0002 — FEAT-GRACE-EVIDENCE-CONTRACTS-MVP

status: rework_required
reviewer: codex
source_hash: sha256:279148232a2c210bcb27dd5b937e55d877ba8756d9dada5ccbc095e70d6a15a0
attempt: attempt-0001
reviewed_at: 2026-05-26

## Verdict

Rework required.

The previous blocker was mostly fixed: runtime evidence is now outside
`EXECUTION_PACKET.md` and stored under `EVIDENCE/attempt-0001/`.

However, the evidence artifact itself is still not clean enough to accept.

## Blocking Issue

### `evidence_manifest.md` contains stale/out-of-scope diff evidence

`EVIDENCE/attempt-0001/evidence_manifest.md` still reports:

```text
automation/cli_health.yaml | 2 +-
```

`automation/cli_health.yaml` is not in the packet's `Allowed Write Scope`.
This appears to be transient CLI health noise, not an implementation change,
but it must not appear in acceptance evidence.

The packet's expected evidence requires a full changed-file list and diff stat
limited to allowed scope. Evidence that includes out-of-scope paths cannot be
accepted, even if the current workspace has since been cleaned.

## Confirmed Passing Checks

I reran exact verification after the source-packet cleanup.

### Targeted Tests

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_evidence_contract.py \
  tests/test_prefect_grace_evidence_manifest.py \
  tests/test_prefect_grace_artifact_validator.py \
  tests/test_prefect_grace_blocker_routing.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_packet_parser.py
```

Result:

```text
85 passed in 2.50s
```

### Regression Tests

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_dag.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_runtime_adapter.py
```

Result:

```text
74 passed in 2.51s
```

### Static / CLI Checks

The following checks passed:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform
python3 -m prefect_grace.cli validate-evidence-contract \
  prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md \
  --json
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md \
  --strict --json
```

## Current Actual Scope Check

After reverting transient `automation/cli_health.yaml`, the actual current
implementation/test diff is limited to allowed paths:

```text
prefect_grace/cli.py
prefect_grace/platform/artifact_validator.py
prefect_grace/platform/blocker_routing.py
prefect_grace/platform/evidence_contract.py
prefect_grace/platform/evidence_manifest.py
prefect_grace/prompts/architect_prompt.md
prefect_grace/prompts/reviewer_prompt.md
prefect_grace/prompts/verifier_prompt.md
tests/test_prefect_grace_artifact_validator.py
tests/test_prefect_grace_blocker_routing.py
tests/test_prefect_grace_cli_contracts.py
tests/test_prefect_grace_evidence_contract.py
tests/test_prefect_grace_evidence_manifest.py
```

Frozen scope check is clean.

## Required Rework

1. Regenerate `EVIDENCE/attempt-0001/evidence_manifest.md` after removing
   transient `automation/cli_health.yaml` from the workspace.
2. Ensure the evidence diff stat and changed-file list contain only allowed
   scope paths.
3. Do not change implementation unless needed; the current code/tests passed.
4. Keep `EXECUTION_PACKET.md` source-contract-only.

## Acceptance Condition

Next review can accept if:

- exact tests remain green;
- evidence manifest no longer mentions `automation/cli_health.yaml` or any
  other out-of-scope file;
- current frozen scope stays clean.
