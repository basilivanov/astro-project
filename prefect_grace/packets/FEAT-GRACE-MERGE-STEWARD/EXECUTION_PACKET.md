# Execution Packet: FEAT-GRACE-MERGE-STEWARD-W01-OPERATOR-APPROVED-FF-MERGE

## Objective

Add a merge steward that turns accepted, pushed packet branches into an
operator-approved merge plan and, when explicitly approved, performs only safe
fast-forward merges in a controlled Git repository.

The steward is separate from nightly execution. It should consume Git mutation
gate outputs, reviews, evidence, and branch state, then provide an auditable
merge summary. No merge should happen by default.

## Slice

- slice_id: `SLICE-GRACE-MERGE-STEWARD`
- slice_slug: `grace-merge-steward`
- feature_id: `FEAT-GRACE-MERGE-STEWARD`
- packet_id: `FEAT-GRACE-MERGE-STEWARD-W01-OPERATOR-APPROVED-FF-MERGE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE, FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD-W01-LIMITS-STOP-CONDITIONS`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-MERGE-STEWARD`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_mutation.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-MERGE-STEWARD`
- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-OPERATOR-JSON`
- `M-GRACE-CLI`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/merge_steward.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_mutation.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_merge_steward.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_merge_steward.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-MERGE-STEWARD/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- Merge steward is dry-run by default.
- Merge apply requires explicit CLI approval and environment token.
- Only fast-forward merge is allowed for first implementation.
- Force push, rebase, squash, reset, branch deletion, tag mutation, and conflict resolution are forbidden.
- Target branch must be explicit, clean, and synchronized.
- Source packet branch must have accepted review, valid evidence, clean scope, and pushed commit proof.
- Merge steward must not start agents, submit Prefect runs, run tests by itself, create worktrees, commit code, push target branch unless explicitly approved, or mutate registry state.
- CLI JSON envelope keeps `result == data`.
- Audit output is bounded.

## Recommended Role Assignment

- coder: `Codex high`; safety-sensitive Git orchestration.
- verifier: `Codex high`; all apply proofs must use temporary Git repos and bare remotes.
- reviewer: `Codex xhigh`; inspect Git commands and approval logic line by line.
- rework policy: fresh session for any merge safety blocker.

## Required Design Decisions

### 1. Steward Inputs

The steward should accept:

- target repo root;
- target branch;
- packet branch names or a saved batch execution summary;
- packet evidence/review locations;
- remote name;
- dry-run/apply flags.

### 2. Planning First

Always build a merge plan before applying. The plan should include:

- merge candidates;
- excluded branches with reasons;
- target branch status;
- fast-forward eligibility;
- evidence/review status;
- approval status;
- planned Git commands as safe descriptors, not raw shell strings.

### 3. Approval Chain

Apply requires:

- `--apply`;
- `--merge`;
- `--i-understand-merge`;
- `GRACE_MERGE_STEWARD_APPROVED=1`;
- clean target branch;
- fast-forward possible;
- all candidates accepted.

### 4. Git Rules

Use argument-list subprocess calls. Do not use shell interpolation. Do not use
destructive commands. Merge apply may use fast-forward-only merge or equivalent
safe ref update in temporary tests, but it must never force-update target.

### 5. Output Shape

Return bounded:

- plan status;
- candidates total and sample;
- excluded total and sample;
- merge applied count;
- target branch before/after SHAs;
- blocker reason;
- warnings/errors.

## Implementation Requirements

1. Add `prefect_grace/platform/merge_steward.py`.
2. Add CLI command such as `merge-steward`.
3. Add temp Git repo tests for dry-run plan, approval missing block, fast-forward merge apply, non-fast-forward block, dirty target block, missing accepted review block, invalid evidence block, and forbidden target branch push.
4. Add CLI contract tests.
5. Add bounded evidence under `EVIDENCE/attempt-0001/`.
6. Do not merge or push real `/opt/astro-project` during verification.

## Acceptance Criteria

- Dry-run produces a merge plan with no Git mutation.
- Missing approval blocks merge.
- Temp-repo fast-forward apply works only with explicit approvals.
- Non-fast-forward, dirty target, missing review, invalid evidence, missing pushed branch, and unsafe paths fail closed.
- No destructive Git command is used.
- Output is bounded and keeps `result == data`.
- Real product branch merge/push is not performed during packet verification.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_merge_steward.py \
  tests/test_prefect_grace_cli_merge_steward.py \
  tests/test_prefect_grace_git_mutation_gate.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/merge_steward.py \
  prefect_grace/cli_commands/git_mutation.py \
  prefect_grace/cli_commands/parser.py \
  prefect_grace/cli.py
```

Run targeted GRACE lint, strict packet validation, temp-repo CLI dry-run proof,
and temp-repo explicit approval fast-forward proof. Do not merge real product
branches.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Temp-repo dry-run merge plan proof.
- Approval-missing blocked proof.
- Temp-repo fast-forward apply proof if implemented.
- Non-fast-forward and dirty-target blocked proofs.
- Confirmation no real product merge/push, live agents, Prefect runs, registry writes, backend, frontend, Docker, Playwright, provider APIs, credentials, or `.worktrees/**` mutation occurred.
- Post-test observability verdict.

## Escalation Triggers

- Merge apply needs force, rebase, squash, reset, checkout of unrelated paths, branch deletion, or conflict resolution.
- Merge can occur without explicit approval.
- Target branch can be pushed or force-updated by default.
- Missing review/evidence/scope proof is accepted.
- Real product branch is merged or pushed during verification.
- Output includes full logs, full diffs, screenshots, or secrets.

## Reviewer Gate

Reviewer must inspect every Git command path and verify that only explicit
operator-approved fast-forward merge is possible.
