# Execution Packet: FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT-W01-ONE-SAFE-ASTRO-PACKET

## Objective

Run one small real Astro packet through the GRACE Prefect-managed pipeline after
the synthetic scratch pilot is accepted.

This packet is the first real product-training step. It should use a low-risk
Astro packet with narrow allowed scope, submit exactly one managed packet flow
run, execute one agent in an isolated worktree, collect bounded evidence and
review, and stop before commit/push/merge unless a later Git packet explicitly
allows branch push.

## Slice

- slice_id: `SLICE-GRACE-SINGLE-ASTRO-PACKET-PILOT`
- slice_slug: `grace-single-astro-packet-pilot`
- feature_id: `FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT`
- packet_id: `FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT-W01-ONE-SAFE-ASTRO-PACKET`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-MANAGED-PREFECT-SCRATCH-RUN, FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-SINGLE-ASTRO-PACKET-PILOT`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-EVIDENCE`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/single_astro_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_single_astro_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_single_astro_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT/**`
- `/tmp/grace-single-astro-packet-pilot/**`

## Frozen Scope

- `/opt/astro-project/backend/** outside selected packet allowed scope`
- `/opt/astro-project/frontend/** outside selected packet allowed scope`
- `/opt/astro-project/prefect_grace/** outside this packet and existing runner commands`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`

## Must Preserve

- Exactly one real Astro packet is selected.
- The selected packet must have narrow allowed scope and no approval-required
  risk flags.
- Dry-run default has zero Prefect runs and zero live agents.
- Real execution requires explicit operator approval and env token.
- Commit, push, and merge are not performed in this packet.
- Backend/frontend services, Docker, Playwright, and deployment are not started
  unless the selected packet verification profile explicitly requires them and
  the operator approves.
- Evidence is bounded.
- CLI JSON envelope keeps `result == data`.

## Required Design Decisions

### 1. Candidate Selection

Pick only a low-risk candidate from the runtime registry or an explicit
`--packet` argument. Reject packets with broad scope, dependency blockers,
missing source hash, missing strict packet contract, or existing blocked review.

### 2. Product Safety

The agent worktree may change only files allowed by the selected packet. The
main checkout remains untouched. Product service start is out of scope unless a
later packet adds that opt-in.

### 3. Stop Before Git Mutation

The pilot may produce accepted/rework evidence and review, but it must not
commit or push. Git mutation belongs to the packet branch push gate.

## Implementation Requirements

1. Add a single Astro pilot module and CLI command.
2. Reuse the managed runner and Prefect submission paths from the scratch pilot.
3. Add candidate filtering for low-risk Astro packets.
4. Add tests for dry-run, missing approval, broad scope rejection, missing
   review/evidence handling, injected live success, injected scope blocked, and
   no Git mutation.
5. Use injected agent/Prefect clients in automated tests.

## Acceptance Criteria

- Dry-run returns one selected low-risk Astro packet or a clear blocker.
- Missing approval starts zero agents and creates zero Prefect runs.
- Injected live success produces bounded evidence/review status.
- Scope violation produces `scope_blocked`, not executor failure.
- No commit, push, merge, registry apply, or source packet mutation occurs.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_single_astro_packet_pilot.py \
  tests/test_prefect_grace_cli_single_astro_packet_pilot.py \
  tests/test_prefect_grace_single_live_packet_pilot.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted lint, strict packet validation, and dry-run proof. Real
live Astro execution requires explicit Architect approval.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Dry-run candidate proof.
- Missing approval blocked proof.
- Injected live success/scope-blocked proof.
- Confirmation no Git mutation, registry apply, product merge, backend,
  frontend, Docker, Playwright, provider secrets, or source packet mutation.

## Escalation Triggers

- Candidate selection picks broad product scope.
- Main checkout is modified.
- Commit/push/merge appears.
- Scope blocker is counted as executor failure.
- Output includes unbounded logs or secrets.
