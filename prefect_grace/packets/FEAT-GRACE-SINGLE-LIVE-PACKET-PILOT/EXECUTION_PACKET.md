# Execution Packet: FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE

## Objective

Add a guarded single-packet pilot runner that can exercise one real GRACE
packet through the live path: selected source packet, isolated worktree,
managed agent execution, scope/evidence/review gates, and the Git mutation gate.

This packet is the first training bridge from deterministic smokes to a real
operator-approved packet run. It must remain single-packet only, dry-run by
default, and fail closed unless the operator explicitly opts into live agent
execution and Git mutation. Merge must stay disabled by default.

The implementation should prove the path with injected/fake runners and
temporary Git repositories. A real live pilot against `/opt/astro-project` must
remain blocked unless the operator supplies explicit approval flags and env
tokens at runtime.

## Slice

- slice_id: `SLICE-GRACE-SINGLE-LIVE-PACKET-PILOT`
- slice_slug: `grace-single-live-packet-pilot`
- feature_id: `FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT`
- packet_id: `FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE, FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-PREFECT-NATIVE-E2E-SUBMISSION-MVP-W01-NATIVE-E2E-SUBMISSION, FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET-W01-LIVE-OPT-IN-SINGLE-SCRATCH`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/live_opt_in_single_scratch_packet.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_live_opt_in_single_scratch_packet.py`

## Impacted Modules

- `M-GRACE-SINGLE-LIVE-PACKET-PILOT`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-PREFECT-SUBMISSION`
- `M-GRACE-LIVE-OPT-IN`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_single_live_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_single_live_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- The pilot runs at most one packet per invocation.
- Dry-run is default and starts no agents, creates no Prefect runs, and performs no Git mutations.
- Live agent execution requires explicit CLI opt-in and an environment token.
- Git commit and push require the Git mutation gate and independent explicit opt-ins.
- Merge is never performed by this pilot command.
- Worktree, state, packet, and evidence roots must be explicit for live tests.
- The main repository checkout must never be used as the agent worktree.
- Scope guard, evidence validation, and accepted review are required before Git mutation.
- CLI JSON envelope keeps `result == data`.
- No backend, frontend, Docker, Playwright, provider APIs, credentials, registry apply, or product merge is used.

## Recommended Role Assignment

- coder: `Codex high`; this is orchestration glue over existing guarded components.
- verifier: `Codex high`; must use injected/fake live runner paths and temp Git repos.
- reviewer: `Codex xhigh`; must verify all live and Git mutation paths fail closed without approvals.
- rework policy: fresh session for opt-in, worktree containment, or Git mutation blockers; light resume for CLI help/evidence formatting.

## Required Design Decisions

### 1. Pilot Command

Add a command such as:

```bash
python3 -m prefect_grace.cli run-single-live-packet-pilot \
  --project prefect_grace/project.yaml \
  --packet prefect_grace/packets/FEAT-X/EXECUTION_PACKET.md \
  --state-root /tmp/grace-single-live/state \
  --worktree-root /tmp/grace-single-live/worktrees \
  --packet-root /tmp/grace-single-live/packets \
  --base-ref prod-release-20260327 \
  --dry-run \
  --json
```

It should select exactly one packet, create/resolve an isolated worktree, run
the managed packet runner when live execution is approved, then call the Git
mutation gate only if commit/push flags are explicitly requested.

### 2. Fail-Closed Live Opt-In

Live agent execution must require:

- `--execute-agent`;
- an acknowledgement flag such as `--i-understand-live-agent`;
- an environment token such as `GRACE_LIVE_AGENT_OPT_IN=1`;
- explicit temp roots or an explicit operator-approved real project mode.

If any are missing, return `ok=false`, `status=blocked`, and
`live_agents_started=0`.

### 3. Git Mutation Opt-In

Commit/push flags must be passed through to `git-mutation-gate`; the pilot must
not shell out to Git directly for mutations. Merge is not exposed in this pilot.

### 4. Evidence And Review Gate

The pilot must refuse Git mutation until packet evidence validates and the
latest review is accepted. It may still report managed runner output in dry-run
or blocked mode.

### 5. Bounded Result

Return bounded summary fields only:

- selected packet id;
- worktree path;
- branch name;
- managed runner status;
- scope status;
- evidence status;
- review status;
- git mutation gate status;
- live agent count;
- Prefect run count;
- blocker reason.

## Implementation Requirements

1. Add `prefect_grace/platform/single_live_packet_pilot.py`.
2. Add CLI command and contract tests.
3. Use dependency injection for managed runner, Prefect submitter, and Git mutation gate in unit tests.
4. Cover dry-run, missing opt-in, injected live success, injected live failure, scope blocked, evidence blocked, review blocked, git gate blocked, and commit/push planned paths.
5. Use temporary Git repositories for any Git mutation proof.
6. Do not run real live agents, real Prefect server, backend, frontend, Docker, Playwright, provider APIs, credentials, registry apply, or product merge during packet verification.

## Acceptance Criteria

- Dry-run returns a deterministic single-packet plan with zero live agents, zero Prefect runs, and zero Git mutations.
- Missing live opt-in blocks live execution before agent launch.
- Injected live success can proceed to evidence/review/git-gate checks.
- Git mutation is delegated to `git-mutation-gate` and is not reimplemented.
- Merge is unavailable or blocked in the pilot.
- Unsafe roots, repo-root worktree paths, missing review, invalid evidence, and scope violations fail closed.
- CLI JSON output is bounded and keeps `result == data`.
- Existing managed runner, Git mutation gate, and live opt-in smoke tests still pass.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_single_live_packet_pilot.py \
  tests/test_prefect_grace_cli_single_live_packet_pilot.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_git_mutation_gate.py \
  tests/test_prefect_grace_live_opt_in_single_scratch_packet.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/single_live_packet_pilot.py \
  prefect_grace/cli_commands/packet_execution.py \
  prefect_grace/cli_commands/parser.py \
  prefect_grace/cli.py
```

Run targeted GRACE lint:

```bash
python3 scripts/grace_lint.py prefect_grace/platform/single_live_packet_pilot.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/packet_execution.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py
python3 scripts/grace_lint.py prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI dry-run proof against temp roots. Do not run live agents, live Prefect,
backend, frontend, Docker, Playwright, provider APIs, credentials, registry
apply, product branch push, or product merge for this packet verification.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- CLI dry-run proof with zero live agents, zero Prefect runs, and zero Git mutations.
- Missing opt-in blocked proof.
- Injected live success/failure proofs.
- Git mutation gate delegation proof.
- Confirmation no real live agent, live Prefect run, registry write, backend, frontend, Docker, Playwright, provider API, credential, product push, product merge, or `.worktrees/**` mutation occurred.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- The pilot needs to run more than one packet.
- The pilot needs to bypass Git mutation gate for commit/push.
- Merge becomes necessary in this packet.
- Live agent can start without explicit approval.
- Git mutation can happen without explicit approval.
- Worktree path can be the repo root or outside explicit worktree root.
- Evidence/review/scope gates can be skipped before Git mutation.
- Real product branch push/merge or registry apply happens during verification.

## Reviewer Gate

Reviewer must verify that the pilot only composes existing gates and does not
create a second hidden Git mutation path.
