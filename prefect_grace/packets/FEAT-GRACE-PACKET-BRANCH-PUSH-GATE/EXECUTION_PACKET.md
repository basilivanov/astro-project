# Execution Packet: FEAT-GRACE-PACKET-BRANCH-PUSH-GATE-W01-ACCEPTED-PACKET-BRANCH-PUSH

## Objective

Add a narrow operator gate that can commit and push exactly one accepted packet
worktree branch after evidence, scope, and review have passed.

The existing Git mutation gate is broad enough to plan commit, push, and merge.
This packet adds the operational wrapper used after the first real Astro packet:
commit and push the packet branch only. Product branch merge remains out of
scope and fail-closed.

## Slice

- slice_id: `SLICE-GRACE-PACKET-BRANCH-PUSH-GATE`
- slice_slug: `grace-packet-branch-push-gate`
- feature_id: `FEAT-GRACE-PACKET-BRANCH-PUSH-GATE`
- packet_id: `FEAT-GRACE-PACKET-BRANCH-PUSH-GATE-W01-ACCEPTED-PACKET-BRANCH-PUSH`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE, FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT-W01-ONE-SAFE-ASTRO-PACKET`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-BRANCH-PUSH-GATE`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_mutation.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-GIT-MUTATION-GATE/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-PACKET-BRANCH-PUSH-GATE`
- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-EVIDENCE`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/packet_branch_push_gate.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/cli_commands/git_mutation.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_branch_push_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_packet_branch_push_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-BRANCH-PUSH-GATE/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Dry-run is default.
- Only commit and push are in scope; merge is not exposed.
- Commit can occur only in the isolated packet worktree, never in the main
  checkout.
- Push can only push `HEAD:<packet_branch>` to the packet branch.
- No force push, tag push, branch deletion, reset, rebase, squash, or target
  branch update.
- Latest review must be accepted and evidence manifest must validate.
- Scope guard must pass.
- CLI JSON envelope keeps `result == data`.

## Required Design Decisions

### 1. Wrapper Over Git Mutation Gate

This packet should delegate mutation to `git_mutation_gate.py`; it must not
implement a second Git mutation engine.

### 2. Preconditions

Fail closed unless:

- packet id matches the packet file;
- worktree is under explicit worktree root;
- branch matches the packet branch pattern;
- changed files are non-empty and scope-accepted;
- evidence validates;
- latest review is accepted;
- commit/push approvals are present.

### 3. No Merge

There should be no merge flag in this wrapper. Merge remains owned by the merge
steward or a later explicit operator step.

## Implementation Requirements

1. Add `prefect_grace/platform/packet_branch_push_gate.py`.
2. Add CLI command such as `packet-branch-push-gate`.
3. Add tests with temporary Git repositories and bare remotes.
4. Cover dry-run, missing review, invalid evidence, scope blocked, wrong branch,
   commit-only apply, push apply, force-push rejection, and merge absence.
5. Keep real repo push blocked unless explicitly approved.

## Acceptance Criteria

- Dry-run shows commit/push plan without mutations.
- Accepted packet branch can be committed and pushed in temp repo tests.
- Missing review/evidence/scope approval blocks mutation.
- Merge is unreachable.
- Audit output is bounded.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_packet_branch_push_gate.py \
  tests/test_prefect_grace_cli_packet_branch_push_gate.py \
  tests/test_prefect_grace_git_mutation_gate.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted lint, strict packet validation, and dry-run CLI proof. Do
not push the real product remote during verification.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Temp bare remote commit/push proof.
- Real repo dry-run proof.
- Confirmation no merge, no force push, no product branch update, no live
  agents, no Prefect runs, no registry writes, and no provider credentials.

## Escalation Triggers

- Product branch can be updated.
- Merge is exposed.
- Scope/evidence/review can be bypassed.
- Destructive Git commands are introduced.
