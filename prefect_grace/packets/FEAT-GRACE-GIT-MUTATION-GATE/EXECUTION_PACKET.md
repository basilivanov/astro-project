# Execution Packet: FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE

## Objective

Add a guarded Git mutation gate for a single already-executed packet worktree.
The gate must decide, in a deterministic and auditable way, whether a packet
worktree is allowed to create a commit, push its packet branch, or prepare a
merge into a target branch.

This is the missing safety layer between managed packet execution and real
operator Git mutations. It must default to dry-run and fail closed unless every
precondition is satisfied. It must not start agents, submit Prefect runs, edit
runtime registry state, or merge into the product branch without a separate
explicit operator opt-in.

The first implementation should prove the full path in temporary Git
repositories, including commit and push to a temporary bare remote. Real repo
merge must remain dry-run/blocked unless all explicit merge approvals are
present.

## Slice

- slice_id: `SLICE-GRACE-GIT-MUTATION-GATE`
- slice_slug: `grace-git-mutation-gate`
- feature_id: `FEAT-GRACE-GIT-MUTATION-GATE`
- packet_id: `FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP-W01-LIFECYCLE-GATE, FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD, FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION-W01-MANIFEST-RELATIVE-ARTIFACTS, FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-GIT-MUTATION-GATE`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/cli_commands/worktrees.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_worktree_manager.py`
- `/opt/astro-project/tests/test_prefect_grace_worktree_scope_lifecycle.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-WORKTREE-MANAGER`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-OPERATOR-JSON`
- `M-GRACE-CLI`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_mutation.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-GIT-MUTATION-GATE/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Dry-run is the default and performs no Git mutations.
- Commit, push, and merge each require explicit independent opt-in flags.
- Commit may only occur inside the isolated packet worktree, never in the main repository checkout.
- Push may only push the packet branch, never the target branch.
- Merge into a target branch must remain fail-closed unless explicit merge approval is present.
- No force push, tag push, branch deletion, reset, rebase, or worktree cleanup is added.
- Scope guard remains the source of truth for changed-file allowed/frozen checks.
- Existing managed runner, worktree scope lifecycle, and nightly dry-run behavior must not change.
- CLI JSON envelope keeps `result == data`.
- Audit output is bounded and suitable for committed evidence.
- No live agents, live Prefect runs, runtime registry writes, backend, frontend, Docker, Playwright, provider APIs, or credentials are used.

## Recommended Role Assignment

- coder: `Codex high`; this is a safety gate around Git mutation.
- verifier: `Codex high`; must use temporary Git repositories and a temporary bare remote.
- reviewer: `Codex xhigh`; review should focus on fail-closed semantics, branch/ref containment, and absence of destructive Git operations.
- rework policy: fresh session for any blocker involving push, merge, branch validation, scope bypass, or destructive Git command; light resume is acceptable for help text, evidence formatting, or missing CLI contract assertions.

## Required Design Decisions

### 1. Add A Pure Planning Layer

Create a platform module such as:

```python
prefect_grace/platform/git_mutation_gate.py
```

The module should expose dataclasses similar to:

```python
GitMutationGatePlan
GitMutationGateResult
```

and a single orchestration function, for example:

```python
run_git_mutation_gate(...)
```

The function must first build a plan and only execute Git mutations when the
matching opt-in flags are present. Dry-run output must show what would happen
without changing the repo.

### 2. Preconditions For Any Mutation

The gate must fail closed unless all of these are true:

- `worktree_path` exists and is a Git worktree;
- `worktree_path` is not the main `repo_root`;
- `worktree_path` is under the explicit `worktree_root`;
- `packet_id` in args matches the parsed `EXECUTION_PACKET.md`;
- current worktree branch matches the expected packet branch pattern:
  `agent/<project_key>/<packet_id>/attempt-<NNNN>`;
- changed files are non-empty for commit, unless the caller explicitly requests
  dry-run status only;
- scope guard passes for changed files against the packet contract;
- no frozen-scope or outside-allowed changes exist;
- no merge conflict markers are present in changed text files;
- required verification evidence exists and validates;
- latest packet review exists and has `accepted` verdict before commit/push/merge.

If any precondition fails, return `ok=false`, `status=blocked`, and a bounded
`blocker_reason`.

### 3. Commit Rules

Commit behavior must:

- default to dry-run;
- require `--commit` and `--apply`;
- run only in `worktree_path`;
- include packet id in the commit message;
- refuse empty commits;
- refuse commits when the worktree branch does not match the packet branch;
- stage only files that scope guard has accepted;
- record the resulting commit SHA;
- never amend, reset, rebase, squash, or commit in `/opt/astro-project`.

### 4. Push Rules

Push behavior must:

- require a successful commit or an existing accepted packet branch commit;
- require `--push` and `--apply`;
- push only `HEAD:<packet_branch>` to the configured remote;
- reject force push and tag push;
- record the remote name, branch name, and pushed commit SHA;
- use temporary bare remotes in tests.

### 5. Merge Rules

Merge behavior must be present as a guarded plan, but real merge must be
harder to enable than commit/push.

Merge must:

- require `--merge`, `--apply`, `--i-understand-merge`, and an environment
  token such as `GRACE_GIT_MERGE_APPROVED=1`;
- require target branch to be explicit;
- require target branch clean and synchronized in the test repo;
- fail closed if fast-forward merge is not possible;
- never merge when source branch is missing, review is not accepted, evidence
  is invalid, scope guard is not clean, or target branch has local changes;
- record merge plan and merge result separately;
- keep real `/opt/astro-project` merge blocked unless the same explicit
  approval checks pass.

The first packet may implement merge as dry-run planning plus temp-repo apply
proof only. If real product merge is still intentionally blocked, report that
as `merge_status=blocked_requires_operator_approval`, not as success.

### 6. CLI Contract

Add a command such as:

```bash
python3 -m prefect_grace.cli git-mutation-gate \
  --packet prefect_grace/packets/FEAT-X/EXECUTION_PACKET.md \
  --repo-root /opt/astro-project \
  --worktree-root /tmp/grace-worktrees \
  --worktree-path /tmp/grace-worktrees/FEAT-X-attempt-0001 \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref prod-release-20260327 \
  --target-branch prod-release-20260327 \
  --remote origin \
  --dry-run \
  --json
```

CLI requirements:

- `--dry-run` default true;
- `--apply` required for any mutation;
- `--commit`, `--push`, and `--merge` are independent explicit flags;
- `--i-understand-merge` is required for merge apply;
- JSON envelope keeps `result == data`;
- non-JSON output remains short and operator-oriented;
- exit code `0` for clean dry-run/apply success, `1` for blocked gate, `2` for command/internal errors.

### 7. Audit Evidence

Every run should return a bounded audit object:

```json
{
  "packet_id": "...",
  "status": "planned|applied|blocked",
  "dry_run": true,
  "mutations": {
    "commit": "planned|applied|blocked|not_requested",
    "push": "planned|applied|blocked|not_requested",
    "merge": "planned|applied|blocked|not_requested"
  },
  "changed_files_total": 3,
  "changed_files_sample": ["..."],
  "commit_sha": null,
  "pushed_ref": null,
  "merge_sha": null,
  "blocker_reason": null
}
```

Do not include full logs, full diffs, screenshots, credentials, remote URLs
with tokens, or unbounded command output.

## Implementation Requirements

1. Add `prefect_grace/platform/git_mutation_gate.py` with deterministic plan/apply logic and no shell interpolation.
2. Add CLI wiring in the split CLI architecture without re-growing `prefect_grace/cli.py` into a monolith.
3. Add unit tests using temporary Git repositories for:
   - dry-run no mutation;
   - commit apply creates one commit only in the packet worktree;
   - push apply pushes only the packet branch to a temp bare remote;
   - merge without explicit approval is blocked;
   - merge with temp-repo approval performs only a fast-forward merge, if implemented;
   - dirty target branch blocks merge;
   - packet branch mismatch blocks commit/push;
   - missing accepted review blocks mutation;
   - invalid evidence manifest blocks mutation;
   - scope violation blocks mutation;
   - absolute/main repo worktree path is rejected.
4. Add CLI contract tests for help text, JSON envelope, dry-run, blocked apply, and exit codes.
5. Add bounded evidence under `EVIDENCE/attempt-0001/`.
6. Do not start live agents, Prefect runs, Docker, backend, frontend, Playwright, provider APIs, or credentialed services.

## Acceptance Criteria

- `git-mutation-gate --dry-run --json` plans commit/push/merge without mutating Git.
- `git-mutation-gate --commit --apply --json` creates a commit only in a temp packet worktree when review/evidence/scope all pass.
- `git-mutation-gate --push --apply --json` pushes only the packet branch to a temp bare remote.
- Merge apply is blocked unless explicit CLI and environment approvals are present.
- Merge planning reports why real merge is blocked when approvals are absent.
- Scope violations, frozen files, missing review, invalid evidence, branch mismatch, dirty target, and unsafe paths all fail closed.
- JSON output is bounded and keeps `result == data`.
- No destructive Git command is used.
- Existing worktree, managed runner, nightly dry-run, and evidence tests still pass.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_git_mutation_gate.py \
  tests/test_prefect_grace_cli_git_mutation_gate.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/git_mutation_gate.py \
  prefect_grace/cli_commands/git_mutation.py \
  prefect_grace/cli_commands/parser.py \
  prefect_grace/cli.py
```

Run targeted GRACE lint:

```bash
python3 scripts/grace_lint.py prefect_grace/platform/git_mutation_gate.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/git_mutation.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py
python3 scripts/grace_lint.py prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-GIT-MUTATION-GATE/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke proofs in temporary Git repositories only:

```bash
python3 -m prefect_grace.cli git-mutation-gate \
  --packet /tmp/grace-git-gate/EXECUTION_PACKET.md \
  --repo-root /tmp/grace-git-gate/repo \
  --worktree-root /tmp/grace-git-gate/worktrees \
  --worktree-path /tmp/grace-git-gate/worktrees/packet-attempt-0001 \
  --project-key astro-project \
  --packet-id FEAT-TEMP-W01-PACKET \
  --attempt 1 \
  --base-ref main \
  --target-branch main \
  --remote origin \
  --dry-run \
  --json
```

Run temp-repo apply proofs for commit and push. Do not run a real
`/opt/astro-project` merge, push to product target branch, live Prefect
submission, live agent, Docker, backend, frontend, Playwright, provider API, or
credentialed service for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- CLI dry-run proof showing no Git mutation.
- Temp-repo commit apply proof with commit SHA.
- Temp bare remote push proof showing only packet branch was pushed.
- Merge blocked proof without explicit approval.
- If merge apply is implemented, temp-repo fast-forward merge proof with explicit approval.
- Scope violation, missing review, invalid evidence, branch mismatch, and unsafe path rejection proofs.
- Confirmation that no real product branch merge/push, live agents, live Prefect runs, registry writes, Docker, backend, frontend, Playwright, provider APIs, credentials, or `.worktrees/**` were touched.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- Commit/push/merge requires weakening scope guard or worktree containment.
- The implementation needs destructive Git commands such as reset, checkout of unrelated paths, rebase, force push, tag push, or branch deletion.
- Commit can happen in `/opt/astro-project` instead of the isolated worktree.
- Push can update the target branch directly instead of the packet branch.
- Merge can occur without explicit CLI and environment approval.
- The gate accepts missing review, invalid evidence, dirty target branch, branch mismatch, or scope violation.
- Real `/opt/astro-project` branch is merged or pushed during verification.
- Backend/frontend/Docker/Playwright/live Prefect/live agent behavior becomes necessary.
- Audit evidence becomes unbounded or includes credentials/raw logs.

## Reviewer Gate

Reviewer must inspect actual Git command construction, not only test results.
Acceptance requires proof that commands are argument-list based, scoped to temp
repos in tests, and cannot perform force push, target-branch push, destructive
cleanup, or unapproved merge.
