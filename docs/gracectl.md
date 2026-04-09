# gracectl CLI Design

**Status:** env/slice/watch/demo commands implemented (2026-03-22). Pending: richer watch dashboards, demo personas, CI hooks.


This document defines the target design for the `gracectl` command-line
interface that orchestrates GRACE slice verification across `/opt/astro-project`.
It captures scope, interfaces, logging formats, failure packets, and command
contracts so that implementation can proceed without additional architectural
decisions.

## Goals and Non-Goals

- **Goals**
  - Provide a single Python CLI (`gracectl`) for running environment diagnostics,
    slice-level verification, log replays, and curated demos.
  - Keep GRACE slice metadata in sync with `docs/GRACE_ARTIFACTS.md` while
    allowing overrides via a dedicated YAML config.
  - Produce deterministic, inspectable logs in
    `test-results/grace-report.json` plus portable failure packets.
  - Reuse existing automation (e.g. `scripts/pipeline.py`,
    `scripts/run_e2e.sh`, `tools/log_watch/*`) instead of duplicating logic.
- **Non-goals**
  - Replacing Playwright, pytest, or docker-compose tooling.
  - Managing infrastructure outside of the local/dev containers.

## Architecture Overview

`gracectl` is a Python 3.11+ application packaged as an internal module and
invoked via `python -m gracectl` or the console entry point installed into the
repo virtualenv.

- **CLI framework**: [`typer`](https://typer.tiangolo.com/) for structured
  commands, options, and help text (click compatibility for easy adoption).
- **Process orchestration**: Thin wrappers around `subprocess.run` with timeout
  + streaming support so scripts such as `scripts/pipeline.py` keep their native
  output.
- **Reporting**: Shared reporter component writes JSON lines to
  `test-results/grace-report.json` and optionally prints rich tables using
  `rich` if installed.
- **Extensibility**: Commands register via Typer sub-apps and can attach custom
  check runners by implementing a `Check` protocol (see “Extension Points”).

### Module & File Layout

```
gracectl/
  __init__.py
  cli.py                # Typer app + entry point wiring
  config.py             # Markdown + YAML parsers, env overrides
  slice_registry.py     # Normalized view of GRACE slices/artifacts
  runners/
    __init__.py
    backend.py          # wrappers for scripts/pipeline.py, targeted pytest
    frontend.py         # wrappers for scripts/run_e2e.sh
    logs.py             # wrappers for tools/log_watch/* and *replay_last.py
  reporters/
    __init__.py
    result_store.py     # grace-report.json writer
    failure_packet.py   # packet assembly utilities
  commands/
    env.py
    slice_verify.py  # contains verify/replay/plan commands
    watch.py
    demo.py
  types.py              # dataclasses for CheckResult, FailurePacket, etc.
```

`pyproject.toml` (or `setup.cfg`) exposes `gracectl=gracectl.cli:app` as the
console entry point. Tests for parsers and reporters live under `tests/gracectl/`.

## Quick Start & Installation

1. Ensure Python 3.11+ is available: `python3 --version`.
2. Create a local virtualenv inside the repo (once):
   ```bash
   python3 -m venv .venv
   ```
3. Activate it for the current shell. On macOS/Linux run
   ```bash
   source .venv/bin/activate
   ```
   (Use `.venv\\Scripts\\activate` on Windows shells.)
4. Install CLI dependencies from the repo root:
   ```bash
   pip install -r requirements.txt
   ```
5. Run `python -m gracectl --help` (or the `gracectl` console script) to verify
   that Typer help renders and the config parser can locate
   `docs/GRACE_ARTIFACTS.md` and `gracectl.yaml`.

Re-activate the virtualenv in every new shell session before invoking the CLI so
all commands pick up the pinned dependencies.

## Daily Command Recipes

The CLI already exposes structured help, but the table below captures the most
common invocations developers run during slice work.

| Workflow | Command | Notes |
| --- | --- | --- |
| Environment validation | `gracectl env check` | Runs docker/container probes plus config parsing; add `--json` for machine-friendly output before CI runs. |
| Slice verification | `gracectl slice verify <SLICE> [--backend] [--frontend]` | Uses the gate profile from markdown + YAML; pass `--plan-only` to inspect required checks without executing. |
| Log replay | `gracectl slice replay <SLICE> [--flow ...] [--limit N]` | Wraps the `tools/*/replay_last.py` helpers referenced by the slice metadata. |
| Log watchers | `gracectl watch run <SLICE>` | Launches CLI scripts defined in top-level `watch.flows[]` (shared pool, filter by slice). Legacy per-slice `watchers` lists were removed in V2. |
| Demos / narratives | `gracectl demo run <SLICE> [--fast] [--replay]` | Chains env check → slice verify → replay for stakeholder-friendly walkthroughs. |

Typical session:

```bash
source .venv/bin/activate
pip install -r requirements.txt   # only when dependencies change
gracectl env check                # make sure docker + docs are ready
gracectl slice verify FEED-PERSONALIZED-DAILY --backend --frontend
gracectl slice replay FEED-PERSONALIZED-DAILY --flow feed --limit 200
gracectl watch run FEED-PERSONALIZED-DAILY
gracectl demo run FEED-PERSONALIZED-DAILY --replay
```

## Log & Failure Artifacts

- `test-results/grace-report.json` — append-only JSON Lines audit trail. Every
  command invocation emits a structured record with start/end timestamps,
  checks, and links back to captured stdout/stderr files.
- `logs/gracectl/` — rolling command logs grouped per slice and runner
  (`backend.pipeline`, `frontend.e2e`, watcher processes, etc.).
- `logs/gracectl/failures/` — expanded failure packets for quick triage. Each
  directory includes `failure.json`, `stdout.log`, `stderr.log`, and any slice
  attachments (screenshots, replay outputs). These paths are referenced from the
  summary objects in `test-results/grace-report.json` and can be zipped for
  external sharing.

Keep both directories under source control ignores so the CLI can freely append
and clean up without polluting commits.

## Configuration & Data Sources

### Primary Source: `docs/GRACE_ARTIFACTS.md`

`gracectl slice *` commands rely on the inventory table inside
`docs/GRACE_ARTIFACTS.md`. The parser must:

1. Locate the “Artifacts Inventory” markdown table (by heading text).
2. Extract rows with columns `Slice`, `Artifact`, `Owner`, `Status`.
3. Normalize slice IDs (e.g. `FORECAST-LADDER-CATALOG-FLIP`).
4. Expand multi-file `Artifact` cells by splitting on `;` and trimming.
5. Associate the `Status` (Ready / In Progress / Baseline doc) to drive
   verification rules.

Implementation detail:

- Use `markdown-it-py` or a lightweight table parser (`tabulate`-style) to avoid
  brittle regexes.
- Cache the parsed result to `.gracectl/cache/artifacts.json` and invalidate on
  source mtime change.

### Override File: `gracectl.yaml`

When slices need richer metadata (test commands, log replays, personas), the
CLI reads `gracectl.yaml` from the repo root. Schema (YAML 1.2):

```yaml
defaults:
  backend_profile: backend:quick
  frontend_profile: frontend:quick
  report_path: test-results/grace-report.json

slices:
  FEED-PERSONALIZED-DAILY:
    status: Ready              # overrides markdown status
    docs:
      - docs/personalized_daily_feed_v2.md
    backend:
      tests:
        - python3 scripts/pipeline.py --select feed
        - python3 -m pytest tests/test_daily_feed_robustness.py -q
    frontend:
      e2e:
        - ./scripts/run_e2e.sh --last-failed
        - ./scripts/run_e2e.sh e2e/core-ux.spec.ts -g "Daily feed"
    logs:
      replay:
        - python3 tools/feed_logs/replay_last.py --limit 200
      watch:
        - python3 tools/log_watch/feed_admin_watch.py --window 15m
    personas:
      - UC-FEED-DAILY
    gate:
      minimum_checks: [backend:quick, frontend:quick]
```

Resolution rules:

1. Parse markdown first to learn available slices.
2. Apply YAML overrides by matching `Slice` keys (case sensitive).
3. Environment variables can override select paths, e.g.
   `GRACECTL_REPORT_PATH`, `GRACECTL_ARTIFACTS=docs/custom.md`.
4. Invalid YAML results in a CLI error that points to the offending key path.

### Runtime Context Detection

`gracectl env check` inspects:

- Docker containers (`astro-project-backend-1`, `astro-project-frontend_dev-1`).
- Python interpreter that runs tests (`PYTHON_EXE`).
- Presence of required documents (`docs/GRACE_ARTIFACTS.md`, `gracectl.yaml`).
- Writable directories (`test-results/`, `logs/`).

These same probes are reused by other commands to fail quickly when the
environment is incomplete.

## Reporting & Failure Packets

### `test-results/grace-report.json`

Append-only JSON Lines file. Each entry documents one CLI invocation or nested
check. Schema:

```json
{
  "grace_version": "1.0.0",
  "generated_at": "2026-03-22T10:00:00Z",
  "command": "slice verify",
  "target": {
    "slice": "FEED-PERSONALIZED-DAILY",
    "profile": "backend:quick",
    "args": ["--backend", "--frontend"]
  },
  "environment": {
    "python": "3.11.8",
    "git_sha": "abc1234",
    "docker": "24.0.5",
    "cwd": "/opt/astro-project"
  },
  "checks": [
    {
      "id": "backend.pipeline",
      "label": "scripts/pipeline.py",
      "status": "passed",
      "duration_ms": 182330,
      "stdout_path": "logs/backend.pipeline.20260322T1000.log"
    },
    {
      "id": "frontend.e2e",
      "label": "./scripts/run_e2e.sh --last-failed",
      "status": "failed",
      "exit_code": 1,
      "duration_ms": 45321,
      "stdout_path": "logs/frontend.e2e.20260322T1000.log",
      "failure_packet": "test-results/failures/feed-daily-20260322T1000.tar.gz"
    }
  ],
  "summary": {
    "status": "failed",
    "passed": 1,
    "failed": 1,
    "skipped": 0
  }
}
```

Implementation notes:

- Reporter writes temp logs in `logs/gracectl/` and references the paths.
- `--json` flag can mirror the same payload to stdout for CI ingestion.

### Failure Packet Format

Derived from GRACE §9.7: the CLI generates a gzipped tarball per failing
command and stores it under `test-results/failures/`.

```
test-results/failures/
  <slice>-<timestamp>/
    failure.json          # structured summary (see below)
    stdout.log            # exact command output
    stderr.log            # separated if available
    artifacts/
      replay.json         # optional structured replay output
      screenshots/...     # optional E2E screenshots
```

`failure.json` schema:

```json
{
  "slice": "FEED-PERSONALIZED-DAILY",
  "scenario": "SCN-FEED-TODAY",
  "gate": "backend:quick",
  "first_divergence": "tests/test_daily_feed_robustness.py::test_push_notifications",
  "observed": "AssertionError: expected 200 got 500",
  "expected": "200 OK with populated cards",
  "probable_scope": ["backend/app/services/personalized_daily.py"],
  "next_steps": ["Inspect personalized_daily.py logs", "Replay feed logs"],
  "attachments": {
    "stdout": "stdout.log",
    "stderr": "stderr.log",
    "replay": "artifacts/replay.json"
  }
}
```

CLI commands attach this packet path to their `CheckResult`. Consumers can zip
the directory or leave it expanded; spec requires at least `failure.json`.

## Command Reference

### 1. `gracectl env check`

| Aspect | Details |
| --- | --- |
| **Purpose** | Assert that local dev containers, dependencies, and config files are present before running slices. |
| **Inputs** | Optional `--profile` (default `full`), `--json` for machine output. |
| **Steps** | 1) Load config; 2) verify Python version & virtualenv; 3) check docker containers (`astro-project-backend-1`, `astro-project-frontend_dev-1`); 4) run `docker exec ... /health` probes (same logic as `scripts/run_e2e.sh`); 5) confirm `scripts/pipeline.py` executable and `docs/GRACE_ARTIFACTS.md` parsable; 6) record results into grace-report. |
| **Outputs** | PASS/FAIL table + JSON entry; failure packet if any probe fails. |
| **Example** | `gracectl env check --json` prints summary and writes `test-results/grace-report.json` entry referencing each probe (`docker.backend.health`, `docs.parse`, etc.). |

### 2. `gracectl slice verify`

| Aspect | Details |
| --- | --- |
| **Purpose** | Run the minimal green profile for a slice (backend quick + targeted E2E). |
| **Inputs** | `gracectl slice verify <slice-id> [--backend/--no-backend] [--frontend/--no-frontend] [--lint] [--plan-only] [--args ...]`. Slice ID matches markdown table entry. |
| **Steps** | 1) Resolve slice metadata (docs, tests, logs) via parser + YAML; 2) determine required gates (defaults to backend quick + frontend quick when `Status` is “In Progress”, backend-only for “Baseline doc”); 3) sequentially run commands:<br>• Backend: `python3 scripts/pipeline.py` or finer-grained pytest commands specified in YAML.<br>• Frontend: `./scripts/run_e2e.sh --last-failed` + optional targeted specs.<br>• Lint/static: `python3 scripts/grace_lint.py` when `--lint` flag is set.<br>4) Surface durations, exit codes, and relevant artifact paths (e.g. `frontend/e2e/*.spec.ts` traces).<br>5) Fail fast if any command returns non-zero, attach failure packet, and stop unless `--keep-going` is passed. |
| **Outputs** | Multi-row status table plus appended grace-report entry listing each sub-check. |
| **Example** | `gracectl slice verify FEED-PERSONALIZED-DAILY --frontend` triggers pipeline + `run_e2e.sh core-ux`, prints a condensed summary, and writes logs under `logs/gracectl/FEED-PERSONALIZED-DAILY/`. |

### 3. `gracectl slice replay`

| Aspect | Details |
| --- | --- |
| **Purpose** | Replay the latest structured logs for a slice to validate business evidence (e.g., feed delivery, admin entitlements, catalog checkout). |
| **Inputs** | `gracectl slice replay <slice-id> [--flow feed|admin|forecast|custom] [--limit 200] [--since 2026-03-20T00:00:00Z]`. Flow defaults derive from YAML `logs.replay` list. |
| **Steps** | 1) Determine replay script per slice (`python3 tools/feed_logs/replay_last.py`, `python3 tools/admin_logs/replay_last.py`, etc.).<br>2) Run script(s) with supplied window/limit.<br>3) Capture JSON output (if script supports `--json`) or parse textual summaries using regex.<br>4) Store structured result into `logs/gracectl/<slice>/replay-*.json` and attach to grace-report entry. |
| **Outputs** | CLI prints key metrics (e.g., “last success at …, alerts: none”), JSON artifact path, optional failure packet if logs missing. |
| **Example** | `gracectl slice replay ADMIN-ENTITLEMENTS-FLOW --flow admin` wraps `python3 tools/admin_logs/replay_last.py --limit 100` and surfaces entitlements anomalies. |

### 4. `gracectl slice plan`

| Aspect | Details |
| --- | --- |
| **Purpose** | Generate a markdown or JSON plan summarizing docs, code, tests, and gates for a slice before implementation. |
| **Inputs** | `gracectl slice plan <slice-id> [--format md|json] [--output docs/slice_plan.md]`. |
| **Steps** | 1) Read slice metadata (docs + tests).<br>2) Enumerate use cases (`UC-*`), scenarios (`SCN-*`), verification IDs, and gating requirements by cross-referencing `requirements.xml` if IDs appear in YAML.<br>3) Format plan with sections: Overview, Artifacts, Required Checks, Log Evidence, Open Risks.<br>4) Optionally persist to disk (default `stdout`). |
| **Outputs** | Text plan ready to paste into `docs/`, plus grace-report entry recording generation time/path. |
| **Example** | `gracectl slice plan FORECAST-LADDER-CATALOG-FLIP --format md --output docs/forecast_plan.md`. |

### 5. `gracectl watch`

_Current state: `watch run` sequentially executes watcher commands defined in top-level `watch.flows[]` (see `gracectl.yaml`). Each flow describes script/args/json/stale metadata and an optional list of slices (`slices: [FEED-PERSONALIZED-DAILY]`). CLI captures exit codes/logs; future revisions will add streaming dashboard, `--flows`, `--refresh`, `--json-stream`._


*(Минимальная реализация: watch run выполняет команды из gracectl.yaml. Далее добавим TUI.)*

*(Minimal implementation: wraps slice-configured watcher commands via `gracectl watch run`. TUI/streaming to follow.)*

| Aspect | Details |
| --- | --- |
| **Purpose** | Tail structured log watchers and summarize flow health continuously. |
| **Inputs** | `gracectl watch run <slice-id>` filters flows to those whose `slices` include the ID (or runs all flows if the list is empty). Future flags will support flows/refresh/json-stream. |
| **Steps** | 1) Load top-level `watch.flows[]` from YAML.<br>2) Select flows matching the slice.<br>3) Render scripts + args and execute, capturing exit code and STDOUT to `logs/gracectl`. |
| **Outputs** | PASS/FAIL summary per watcher plus grace-report entry. Future versions will stream live dashboards. |
| **Example** | `gracectl watch run FEED-PERSONALIZED-DAILY`. |

**Watch flow config example**

```yaml
watch:
  flows:
    - id: FLOW-BILLING
      label: "Billing & Credits"
      script: PYTHONPATH=. python3 tools/log_watch/billing_watch.py
      args:
        --billing-log: logs/billing.jsonl
        --window-minutes: 20
        --json: true
      json_output: true
      stale_after: 30m
      slices: [FORECAST-LADDER-CATALOG-FLIP]
```

Watcher scripts emitting JSON (e.g., `billing_watch.py`) should include a `block` field that mirrors the flow ID so future TUIs/CI parsers can correlate payloads with `watch.flows[]` rows.

### 6. `gracectl demo`

_Current state: `demo run` performs optional `env check`, then `slice verify` (backend/frontend flags) и `slice replay`. Personas/advanced scripting остаются TODO._


*(Current functionality: `demo run` выполняет env check (если не `--fast`), затем backend/frontend verify и replay. Персональные сценарии и нарратив добавим позже.)*

| Aspect | Details |
| --- | --- |
| **Purpose** | Showcase end-to-end slice health by chaining env check → verify → replay with curated sample inputs. |
| **Inputs** | `gracectl demo run <slice-id> [--fast] [--backend/--no-backend] [--frontend/--no-frontend] [--replay/--no-replay]`. |
| **Steps** | 1) Optional `env check`.<br>2) Run `slice verify` with requested sections.<br>3) Optionally run `slice replay`. |
| **Outputs** | PASS/FAIL summary recorded in grace-report. Future versions will append narrative + persona metadata. |
| **Example** | `gracectl demo run FEED-PERSONALIZED-DAILY --backend --no-frontend --replay`. |

## Integration with Existing Scripts

- **Backend pipeline**: `runners/backend.py` shells out to
  `python3 scripts/pipeline.py`. Optional `--select` flag lets YAML override the
  command for slices needing fewer tests.
- **Targeted pytest**: Additional backend tests defined in YAML run via the same
  runner; results aggregated under `check.id = backend.pytest::<module>`.
- **Frontend E2E**: `runners/frontend.py` executes `./scripts/run_e2e.sh` with
  slice-specific arguments (e.g., `--last-failed`, `e2e/report-create.spec.ts`).
- **Log helpers**: `runners/logs.py` wraps `tools/feed_logs/replay_last.py`,
  `tools/admin_logs/replay_last.py`, and watchers from `tools/log_watch/`.
  Their outputs feed into `slice replay` and `watch` commands, ensuring the CLI
  is a thin orchestrator instead of duplicating parsing logic.
- **Benchmark harness**: `gracectl demo` can optionally call
  `python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/...`
  when the slice YAML lists a `benchmark` entry.

## Extension Points

1. **Check plugins**: Any module can register a `CheckSpec` with fields
   (`id`, `label`, `command`, `env`, `parser`). Additional commands (e.g.,
   security scans) can reuse the same execution pipeline by adding entries in
   YAML.
2. **Custom log replays**: Provide new scripts, add to `logs.replay`, and the
   CLI automatically surfaces them under `slice replay` via naming convention.
3. **Report consumers**: `gracectl --json` outputs the same payload as the
   stored JSON line, enabling CI or bots to react without parsing log files.
4. **Skill hooks**: Future skills (per `skills/` directory) can call `gracectl`
   subcommands; design keeps arguments deterministic and documented.

## Sample Outputs

### Env Check (text mode)

```
$ gracectl env check
┌─────────────────────────────┬────────┬────────────┐
│ Probe                       │ Status │ Duration   │
├─────────────────────────────┼────────┼────────────┤
│ python.version>=3.11        │ PASS   │ 0.1s       │
│ docker.backend.health       │ PASS   │ 1.8s       │
│ docker.frontend.health      │ PASS   │ 1.6s       │
│ docs.GRACE_ARTIFACTS.parse  │ PASS   │ 0.2s       │
│ gracectl.yaml.load          │ WARN   │ missing    │
└─────────────────────────────┴────────┴────────────┘
Summary: PASS with warnings (using markdown defaults)
Report: test-results/grace-report.json (entry #42)
```

### Slice Verify (JSON excerpt)

```json
{
  "command": "slice verify",
  "target": {"slice": "FORECAST-LADDER-CATALOG-FLIP"},
  "checks": [
    {"id": "backend.pipeline", "status": "passed", "duration_ms": 182330},
    {"id": "frontend.e2e.report-create", "status": "failed", "failure_packet": "test-results/failures/forecast-20260322T1210.tar.gz"}
  ]
}
```

### Slice Replay (text mode)

```
$ gracectl slice replay ADMIN-ENTITLEMENTS-FLOW --flow admin
Flow admin.entitlements
  Last success: 2026-03-21T19:32:14Z (checkout_success user_id=530)
  Alerts: none in last 120 records
Artifacts: logs/gracectl/ADMIN-ENTITLEMENTS-FLOW/replay-20260322T1200.json
```

## Implementation Notes

- **Error handling**: Each command raises `rich`-formatted exceptions with clear
  remediation hints; fatal errors always produce failure packets.
- **Concurrency**: `slice verify` runs checks sequentially by default; `--parallel`
  flag can enable `asyncio`-based concurrency for independent tests (frontend vs
  backend) once stability is proven.
- **Permissions**: Commands respect `GRACECTL_NO_DOCKER=1` to skip container
  checks when running in CI.
- **Testing**: Unit tests cover parsers and failure-packet assembly; integration
  tests can mock subprocesses to assert reporter output.

## Next Steps

1. Implement config parser + registry scaffolding.
2. Stub commands with Typer and wire environment detection.
3. Incrementally connect backend/frontend runners, followed by replay + watch.
4. Dogfood `env check` + `slice verify` for `FEED-PERSONALIZED-DAILY` before
   rolling to other slices.
