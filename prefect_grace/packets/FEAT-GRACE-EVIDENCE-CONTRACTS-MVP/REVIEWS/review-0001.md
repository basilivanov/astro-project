# Review 0001 — FEAT-GRACE-EVIDENCE-CONTRACTS-MVP

status: rework_required
reviewer: codex
source_hash: sha256:381258b861108e115e28e9b4b7ee371c6ba11a68cf368841265c243244f9f471
attempt: attempt-0001
reviewed_at: 2026-05-26

## Verdict

Rework required.

The implementation and tests are directionally acceptable, but the packet cannot
be accepted because runtime evidence was written into `EXECUTION_PACKET.md`
instead of packet-local runtime artifact files.

This violates the artifact layout rule established by the platform:

```text
EXECUTION_PACKET.md = source contract only
EVIDENCE/attempt-N/* = runtime verification evidence
REVIEWS/review-N.md = reviewer verdicts
REWORK/attempt-N.md = rework instructions
```

## Blocking Issue

### Evidence is embedded in the source contract

The packet directory currently contains only:

```text
prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md
```

There is no `EVIDENCE/attempt-0001/` directory with verification artifacts.
At the same time, `EXECUTION_PACKET.md` contains appended evidence sections such
as:

- `## Evidence`;
- `## Git Diff Statistics`;
- `## Changed Files`;
- test outputs;
- CLI smoke outputs;
- examples and confirmations.

That makes the source contract mutable and bloated. It also breaks source-hash
semantics: future runtime evidence would change the packet contract hash and
could incorrectly invalidate coder/reviewer resume decisions.

## Confirmed Passing Checks

I reran the exact verification commands from the packet.

### Targeted Evidence Contract Tests

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
85 passed in 2.55s
```

### MVP Regression Tests

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
74 passed in 2.84s
```

### Static And CLI Checks

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

## Required Rework

1. Create packet runtime artifact directory:

   ```text
   prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EVIDENCE/attempt-0001/
   ```

2. Move runtime evidence out of `EXECUTION_PACKET.md` into bounded files under
   that directory, for example:

   ```text
   pytest_targeted.txt
   pytest_regression.txt
   compileall.txt
   grace_lint_platform.txt
   cli_validate_evidence_contract.json
   cli_validate_packet.json
   git_diff_stat.txt
   git_diff_name_only.txt
   examples.md
   confirmations.md
   evidence_manifest.json
   ```

3. Restore `EXECUTION_PACKET.md` to source-contract-only content:

   - keep objective/scope/verification/expected evidence/reviewer gate;
   - remove appended runtime evidence output;
   - do not leave test logs, CLI JSON, or diff output in the source packet.

4. Re-run `validate-packet --strict --json` and record the new source hash.

5. Re-run the exact verification commands or copy the already passing command
   outputs into `EVIDENCE/attempt-0001/` if they are unchanged and still valid.

6. Keep implementation scope unchanged. Do not change product backend/frontend,
   live agents, Prefect flows, or launcher behavior as part of this rework.

## Acceptance Condition

The next review can accept the packet if:

- exact verification still passes;
- `EXECUTION_PACKET.md` no longer contains runtime evidence;
- `EVIDENCE/attempt-0001/` contains the verification artifacts;
- `git diff --name-only` evidence is limited to allowed scope;
- no frozen scope is modified.
