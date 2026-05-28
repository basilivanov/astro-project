# Review 0001 - FEAT-GRACE-PACKET-BRANCH-PUSH-GATE

status: rework_required
reviewer: codex
source_hash: sha256:0d60a955b4d08e6f439044c936bcc344f655b964cb831118162678dd929762b5
reviewed_commit: dc06b16 + uncommitted implementation
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The wrapper is correctly structured as a narrow facade over
`git_mutation_gate.py`, the CLI does not expose merge, and the normal
commit+push temp-remote path works. However, push-only apply can bypass scope
validation when the packet branch already contains committed changes. That
violates the packet branch push gate contract.

No product remote, live agent, Prefect run, registry apply, backend/frontend,
Docker, Playwright, or provider call was used during review.

## Blockers

1. Push-only apply can push an already committed out-of-scope diff.

   `run_packet_branch_push_gate()` delegates push-only requests directly to
   `run_git_mutation_gate()` with `commit=False`, `push=True`, and `merge=False`
   (`prefect_grace/platform/packet_branch_push_gate.py:191` through `:208`).
   The delegated gate calculates scope from porcelain worktree status only
   (`prefect_grace/platform/git_mutation_gate.py:326` through `:340`). If the
   packet branch is clean but already contains committed out-of-scope changes,
   `changed_files` is empty, scope validation passes, and `_apply_push()` pushes
   `HEAD` to the packet branch (`prefect_grace/platform/git_mutation_gate.py:390`
   through `:394`).

   Reproducer in a temporary repo/bare remote:

   ```text
   worktree_status= ''
   ok= True
   status= applied
   mutations= {'commit': 'not_requested', 'push': 'applied', 'merge': 'not_available'}
   blockers= []
   changed_files_total= 0
   remote_ref_returncode= 0
   ```

   The branch contained a committed `frozen/already_committed.txt` change, but
   the wrapper still pushed it because no uncommitted worktree change was
   present.

   This violates the required preconditions in `EXECUTION_PACKET.md:96` through
   `:102`: changed files must be non-empty and scope-accepted before mutation.
   It also violates the escalation trigger at `EXECUTION_PACKET.md:154`
   (`Scope/evidence/review can be bypassed`).

   Required fix: before any push apply, validate the committed packet branch
   diff against `base_ref` or otherwise fail closed unless the commit was
   applied in the same invocation after scope validation. The safer approach is
   to compute the branch diff, validate it with `scope_guard`, require it to be
   non-empty, and block push if committed changes are outside allowed/frozen
   scope. Add regression coverage for a clean worktree with an already
   committed out-of-scope file and for a valid already-committed in-scope
   push-only branch if push-only is meant to remain supported.

## Verification Reviewed

- Packet-specified pytest profile:
  `59 passed in 16.11s`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint:
  `packet_branch_push_gate.py`, `git_mutation.py`, and `parser.py` passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`; artifact validation passed, with
  non-blocking `unknown_evidence_id` warnings from the current evidence
  contract parser.
- Scope check against the packet allowed scope: `ok=true`,
  `outside_allowed=[]`, `frozen_violations=[]`.
- Independent temp repro proved the push-only committed-diff scope bypass.

## Observability Verdict

unexpected-degradation.

The normal happy path evidence is bounded and clean, but the push-only safety
case is not fail-closed. The implementation must not be accepted until committed
branch diffs are scope-validated before push.
