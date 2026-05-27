# Execution Packet: FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT

## Objective

Split `prefect_grace/cli.py` into GRACE-canon command modules without changing
CLI behavior.

The current CLI file is a central orchestration bottleneck: it has 2664 physical
lines, lacks GRACE module contracts, and its `build_parser()` function exceeds
the local function size guard. Real seeded Prefect and live opt-in smoke work
will add more commands, so the CLI must become a small facade before those
real-run packets are implemented.

This packet is extraction-only. It must not change command names, defaults,
JSON envelopes, exit codes, safety gates, runtime semantics, or any product
Astro behavior.

## Slice

- slice_id: `SLICE-GRACE-CLI-COMMAND-MODULE-SPLIT`
- slice_slug: `grace-cli-command-module-split`
- feature_id: `FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT`
- packet_id: `FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT-W01-FEATURE-PIPELINE-MODULE-SPLIT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/scripts/check_size_limits.py`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_handoff.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_manager.py`

## Impacted Modules

- `M-GRACE-CLI`
- `M-GRACE-CLI-PARSER`
- `M-GRACE-CLI-COMMANDS`
- `M-GRACE-OPERATOR-JSON`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-WORKTREE-LIFECYCLE`
- `M-GRACE-SIZE-GUARD`

## Required Design Decisions

### 1. CLI Facade Stays Stable

`prefect_grace/cli.py` must remain the public module and executable entrypoint:

```bash
python3 -m prefect_grace.cli ...
```

It must continue to expose:

- `build_parser()`;
- `main()`;
- `_json_envelope(...)`;
- private `_cmd_*` compatibility names that existing tests or callers import.

The implementation may turn these names into imports or thin wrappers, but
their callable behavior must stay compatible.

### 2. Extract Command Groups, Not Runtime Behavior

Move CLI command handlers and parser registration into focused modules. The
packet must not change the underlying platform, flow, task, registry, Prefect,
agent, worktree, evidence, or smoke behavior.

The only allowed behavior-affecting changes are bug-compatible import fixes
needed to keep the same behavior after extraction.

### 3. Target Module Layout

Preferred layout:

```text
prefect_grace/
  cli.py
  cli_commands/
    __init__.py
    common.py
    parser.py
    legacy_feature.py
    project_registry.py
    packet_submission.py
    prefect_smokes.py
    worktrees.py
    packet_execution.py
    evidence.py
    executors.py
```

The implementation may adjust file names if the final grouping is clearer, but
it must avoid catch-all `utils.py` modules.

Suggested grouping:

- `common.py`: JSON envelope, printing, shared argument actions, safe helpers;
- `parser.py`: `build_parser()` orchestration plus small `register_*` calls;
- `legacy_feature.py`: existing feature/test-feature/submit-feature commands;
- `project_registry.py`: validate/scan/sync/bootstrap/status/dump commands;
- `packet_submission.py`: `submit-packets` command;
- `prefect_smokes.py`: existing Prefect smoke commands;
- `worktrees.py`: worktree create/status/cleanup/scope commands;
- `packet_execution.py`: managed packet, E2E packet, E2E flow, handoff commands;
- `evidence.py`: review/evidence/rework/evidence-contract commands;
- `executors.py`: executor listing/selection commands.

### 4. Size Guard Is A Hard Acceptance Gate

After the refactor, this command must pass for `cli.py` and all new CLI command
modules:

```bash
python3 scripts/check_size_limits.py \
  --root prefect_grace/cli.py \
  --max-file-lines 1000 \
  --max-function-tokens 4000

python3 scripts/check_size_limits.py \
  --root prefect_grace/cli_commands \
  --max-file-lines 1000 \
  --max-function-tokens 4000
```

`prefect_grace/cli.py` target:

- under 600 physical lines if practical;
- hard limit under 1000 physical lines;
- no function over 4000 tokens.

Every new CLI command module must be under 1000 physical lines and must have no
function over 4000 tokens.

### 5. Parser Semantics Must Not Drift

All existing command names, aliases, flags, choices, defaults, required flags,
help strings, destination names, and `set_defaults(func=...)` behavior must stay
stable unless an existing test proves the current behavior is wrong and the
packet explicitly documents the compatibility-safe correction.

Special safety-sensitive flags must be preserved exactly:

- `submit-packets --execute` and `--dry-run`;
- `--runner e2e|managed`;
- `--execute-agent`;
- `--no-dry-run`;
- `--allow-live-agent-smoke`;
- smoke `--state-root`, `--worktree-root`, and `--packet-root` flags;
- all `--json` flags.

### 6. JSON Envelope Must Stay Stable

Every JSON command covered by this packet must keep the existing envelope:

```json
{
  "ok": true,
  "project_key": "astro-project",
  "command": "...",
  "result": {},
  "data": {},
  "warnings": [],
  "errors": []
}
```

For existing commands, `result` must remain equal to `data`.

No command may print secrets, raw env values, provider credentials, or unredacted
tokens.

### 7. Safety Gates Must Not Open

The split must not make any dry-run command execute live work. In particular:

- `submit-packets --dry-run` must not create Prefect runs;
- real dry-run smoke must keep `execute_agent=false`;
- live-agent flags must remain fail-closed unless their existing explicit gates
  allow them;
- no Codex, Claude, agy, provider API, Docker, backend, frontend, or Playwright
  execution may start in tests.

### 8. GRACE Canon Contracts For New Modules

Every new CLI command module must pass `scripts/grace_lint.py` and include:

- `AI_HEADER`;
- `START_MODULE_CONTRACT` / `END_MODULE_CONTRACT`;
- `START_MODULE_MAP` / `END_MODULE_MAP`;
- function contracts for public functions.

`prefect_grace/cli.py` must also be brought under this canon discipline as a
facade module.

### 9. No Product Or Runtime State Writes

This refactor must not mutate:

```text
backend/**
frontend/**
prefect_grace/state/*.yaml
/var/lib/grace-orchestrator/**
```

Tests must use mocks or temp roots where command execution requires state.

## Required Implementation Shape

Recommended extraction order:

1. Add `prefect_grace/cli_commands/common.py` and move JSON envelope / shared
   helpers while keeping imports in `prefect_grace.cli` compatible.
2. Add focused command modules and move `_cmd_*` functions by command family.
3. Add `prefect_grace/cli_commands/parser.py` with small `register_*` functions.
4. Replace `prefect_grace.cli.build_parser()` with a facade call into parser
   assembly.
5. Keep compatibility aliases in `prefect_grace.cli` for every moved `_cmd_*`
   function that tests or callers may import.
6. Run targeted CLI contract tests after each command-family move.
7. Run size guard and GRACE lint after the final move.

The packet must not implement new commands for future seeded/live smokes. It may
leave extension points that make those later commands easy to add.

## Required Compatibility Inventory

Before editing, record an inventory of:

- every CLI subcommand name;
- every flag and alias per command;
- required/default/choice/dest values for safety-sensitive flags;
- every function currently exposed by `prefect_grace.cli` and referenced by
  tests;
- every JSON command envelope covered by tests.

After editing, tests must prove the inventory did not drift.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/__init__.py`
- `/opt/astro-project/prefect_grace/cli_commands/common.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/legacy_feature.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/worktrees.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/prefect_grace/cli_commands/executors.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_command_module_split.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_batch_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_live_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_handoff.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_manager.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_scope_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_scope_lifecycle.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_scope_guard.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/platform/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/check_size_limits.py`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- `python3 -m prefect_grace.cli` remains the executable entrypoint.
- Existing command names and aliases remain available.
- Existing parser defaults, choices, destinations, and required flags remain stable.
- Existing CLI JSON envelope fields remain stable: `ok`, `project_key`, `command`, `result`, `data`, `warnings`, `errors`.
- `result == data` for existing JSON commands.
- Compatibility imports from `prefect_grace.cli` keep working for moved `_cmd_*` functions and `build_parser()`.
- `submit-packets --dry-run` creates no Prefect runs.
- Live-agent execution remains fail-closed behind existing explicit gates.
- No live agents, Prefect live runs, Docker, backend, frontend, Playwright, or provider APIs are started by tests.
- No source packet, runtime registry, `prefect_grace/state/*.yaml`, or `/var/lib/grace-orchestrator/**` path is mutated by the refactor.
- Product backend/frontend files remain untouched.

## Verification

Run targeted CLI tests:

```bash
pytest -q \
  tests/test_prefect_grace_cli_command_module_split.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py \
  tests/test_prefect_grace_cli_prefect_e2e_batch_smoke.py \
  tests/test_prefect_grace_cli_prefect_e2e_live_smoke.py \
  tests/test_prefect_grace_cli_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_e2e_packet_flow.py \
  tests/test_prefect_grace_cli_handoff.py \
  tests/test_prefect_grace_cli_managed_packet_runner.py \
  tests/test_prefect_grace_cli_worktree_manager.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py \
  tests/test_prefect_grace_cli_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_scope_guard.py
```

Run smoke parser commands that do not mutate state:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.md \
  --strict --json

python3 -m prefect_grace.cli validate-project \
  --project prefect_grace/project.yaml \
  --json
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/cli.py prefect_grace/cli_commands

python3 scripts/grace_lint.py prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/cli_commands

python3 scripts/check_size_limits.py \
  --root prefect_grace/cli.py \
  --strict \
  --max-file-lines 1000 \
  --max-function-tokens 4000

python3 scripts/check_size_limits.py \
  --root prefect_grace/cli_commands \
  --strict \
  --max-file-lines 1000 \
  --max-function-tokens 4000
```

Run focused parser inventory assertions:

```bash
pytest -q tests/test_prefect_grace_cli_command_module_split.py -k "parser or inventory or compatibility"
```

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, live
agents, or provider APIs for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted CLI pytest output.
- Compile output for `prefect_grace/cli.py` and `prefect_grace/cli_commands`.
- `scripts/grace_lint.py` output for `prefect_grace/cli.py` and `prefect_grace/cli_commands`.
- `scripts/check_size_limits.py` output proving `cli.py` and new command modules are under 1000 lines and 4000 function tokens.
- Parser inventory before/after summary.
- List of moved `_cmd_*` functions and their destination modules.
- Confirmation that `build_parser()` remains import-compatible.
- Confirmation that safety-sensitive flags did not drift.
- Confirmation that no source packets, runtime registry, `prefect_grace/state/*.yaml`, real `/var/lib/grace-orchestrator/**`, backend, frontend, live agents, Docker, or Playwright were touched.

## Escalation Triggers

- Any command default, alias, destination, or safety-sensitive flag must change.
- Existing tests depend on private `prefect_grace.cli` functions that cannot be preserved as compatibility aliases.
- Extraction requires modifying platform, flow, task, backend, or frontend code.
- `cli.py` cannot be brought under 1000 lines without moving behavior.
- `build_parser()` cannot be brought under 4000 tokens without changing parser semantics.
- A new command module would exceed 1000 lines or contain a function above 4000 tokens.
- `submit-packets --dry-run` starts creating Prefect runs.
- Any live-agent path becomes easier to trigger.

## Reviewer Gate

Reviewer must reject this packet if:

- `prefect_grace/cli.py` remains above 1000 lines;
- `build_parser()` or any new function exceeds 4000 tokens;
- new CLI modules fail GRACE lint;
- any existing command disappears or changes parser contract unexpectedly;
- JSON envelope fields change for existing commands;
- `result != data` for covered JSON commands;
- compatibility imports from `prefect_grace.cli` break;
- `submit-packets --dry-run` creates Prefect runs;
- live-agent safety gates are weakened;
- platform, flow, task, backend, frontend, scripts, state, or real runtime files
  are modified outside allowed scope;
- live agents, live Prefect submissions, Docker, backend, frontend, Playwright,
  or provider APIs are started.
