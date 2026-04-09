# gracectl Watch & Demo Extensions

**Status:** Draft specification (2026-03-22). Owners: gracectl maintainers.

This document extends `docs/gracectl.md` with detailed behavior for the
upcoming **watch TUI/json-stream** features and **demo persona scripts**. The
spec enumerates CLI contracts, data structures, and integrations with existing
automation such as `tools/log_watch/*.py` and the slice automation map.

## Scope & Goals

- Upgrade `gracectl watch` from ad-hoc sequential command runners to a
  structured status dashboard (TUI) that can also emit machine-friendly JSON
  streams for bots.
- Introduce configurable demo personas per slice so `gracectl demo` can run
  narrative scenarios, capture evidence, and store replay artifacts.
- Preserve compatibility with current YAML configuration and watcher scripts
  while adding new sections for flows/personas.
- Provide clear extension points for future CI/web surfaces.

Non-goals: reimplement the watcher Python scripts, replace Playwright/pytest,
or build a hosted dashboard.

## Implementation Roadmap (MVP → Beta)

1. **Config groundwork (Day 0–1)**
   - Extend `gracectl/config.py` to parse `watch.flows[]` + `demo.personas[]` with validation helpers.
   - Ship schema docs + sample YAML so existing commands continue to load.
2. **Watch collectors (Day 1–2)**
   - Introduce `LogWatcherRunner` with async execution + JSON parsing fallback.
   - Add cache writer + minimal alert evaluation (stale, exit ≠ 0).
3. **TUI & JSON stream (Day 2–3)**
   - Build `watch tui` event loop using `rich.Live` / hotkeys; gate layout behind feature flag.
   - Reuse runner outputs for `watch json-stream` CLI; emit `.jsonl` snapshots + exit codes.
4. **Persona dispatcher (Day 3–4)**
   - Define `DemoPersona`, `DemoStep`, `DemoReport` dataclasses + evidence layout helpers.
   - Implement `gracectl demo run/list/record` scaffolding.
5. **Reporting + docs (Day 4–5)**
   - Integrate reporter hooks, templated markdown output, automation map references.
   - Update `docs/gracectl.md`, add smoke personas for three flagship slices.

Each milestone is independently deployable (e.g., config parsing can land without the TUI) so we can dogfood the stream API before graphical polish.

## Watch/TUI Execution Plan (Pseudocode)

```python
def watch_main(mode: Literal["tui", "json"], args: WatchArgs):
    cfg = load_config(args.config_path)
    flows = resolve_flows(cfg, slice_id=args.slice_id, filters=args.flows)
    runner = LogWatcherRunner(flows, max_window=args.max_window)
    stream = JsonStreamWriter(args.json_stream) if args.json_stream else None

    def tick() -> SliceWatchSnapshot:
        raw = runner.collect_snapshot()
        if stream:
            stream.write(raw)
        return raw

    if mode == "json":
        snapshot = tick()
        exit(0 if snapshot.summary.status == "healthy" else 2)

    tui = WatchTUI(refresh=args.refresh, flows=flows)
    tui.render(tick())
    while tui.should_continue:
        action = tui.wait_for_input(timeout=args.refresh)
        if action == "refresh":
            tui.render(tick())
        elif action == "filter":
            flows = tui.prompt_filter()
            runner.update_filters(flows)
        elif action == "quit":
            break
    tui.shutdown()
```

Key supporting behaviors:

- `LogWatcherRunner.collect_snapshot()` gathers watchers concurrently, merges multiplexed outputs, annotates freshness deltas, and attaches diagnostics when scripts exceed SLA.
- `JsonStreamWriter` appends newline-delimited JSON, rotates files when `--json-stream` points to disk, and mirrors payloads to STDOUT when requested.
- `WatchTUI` caches the latest snapshot so quick key presses (`r`, `f`) do not block on in-flight watcher executions.

### JSON Stream Emission Flow

```python
class JsonStreamWriter:
    def __init__(self, target: str | Path):
        self.handle = sys.stdout if target == "-" else open(target, "a", buffering=1)

    def write(self, snapshot: SliceWatchSnapshot):
        payload = snapshot.to_dict()
        payload["schema"] = "gracectl.watch/1"
        line = json.dumps(payload, default=isoformat)
        self.handle.write(line + "\n")
```

- When invoked via `watch json-stream`, the CLI executes one `tick()` and relies solely on the exit code for CI gates.
- `watch tui --json-stream path` reuses the same writer, ensuring both human UI and automation share identical payloads.

## Config Schema (Watch + Demo)

| Section | Field | Type | Notes |
| --- | --- | --- | --- |
| `watch.flows[].id` | string | Required | Unique per slice, used in filters/UI rows. |
| `watch.flows[].script` | string | Required | Executable command (with args) evaluated via `shlex.split`. |
| `watch.flows[].args` | dict`<flag,value>` | Optional | Rendered into CLI args preserving insertion order. |
| `watch.flows[].stale_after` | duration string | Optional | Overrides global freshness window per flow. |
| `watch.flows[].json_output` | bool | Optional | Enables JSON parsing; fallback uses stdout heuristics. |
| `watch.flows[].multiplex` | list[string] | Optional | Splits one watcher into many `FlowStatus` entries. |
| `demo.personas[].steps[].type` | enum | Required | `backend`, `ui`, `replay`, `evidence`, `note`. |
| `demo.personas[].steps[].checks` | list[string] | Conditional | Maps to automation map IDs or explicit commands. |
| `demo.personas[].report.template` | path | Optional | Jinja template; default scaffold used if absent. |
| `demo.personas[].report.output` | path | Optional | Target markdown destination; defaults to evidence dir. |

All new keys live under existing slice entries, so enabling the feature is as simple as adding `watch:`/`demo:` blocks to the YAML without touching other slices.

## Watch Command Extensions

### CLI Surface

```
gracectl watch tui <slice-id>
  [--config gracectl.yaml]
  [--flows feed,admin]
  [--refresh 5s]
  [--json-stream logs/gracectl/watch.jsonl]
  [--max-window 30m]

gracectl watch json-stream <slice-id>
  [--flows *]
  [--max-window 30m]
  --output - | path

gracectl watch run <slice-id>  # existing command kept for scripting
```

- `--flows`: comma-separated list of flow IDs (matching YAML definitions) to
  focus on. Defaults to all flows defined for the slice; `*` means aggregate
  across slices.
- `--refresh`: polling cadence for the TUI. Accepts `<int>s` / `<int>m` (default
  10s). A zero refresh renders once and exits.
- `--json-stream`: when provided, the TUI writes each refresh payload as a JSON
  object to either STDOUT (`-`) or a file for bots to ingest (e.g., Slack hooks).
- `--max-window`: overrides the acceptable “last success” age fed to watcher
  scripts; defaults to their own CLI flags when omitted.

### Data & UI Model

- **FlowStatus schema** *(one per flow row)*:
  - `flow_id`, `label`, `source_script` (e.g., `tools/log_watch/feed_admin_watch.py`).
  - `last_event_at`, `last_event`, `last_stage/surface`, `records_checked`.
  - `last_success_at`, `minutes_since_success`, `last_success_event`.
  - `last_error_at`, `last_error_event`, `alerts[]`.
  - `log_path`, `exit_code`, `latency_ms` from watcher invocation.
- **SliceWatchSnapshot** *(per refresh)*:
  - `generated_at`, `slice`, `flows[]`, `summary.status` (`healthy/degraded`),
    `summary.alert_count`, `summary.oldest_success_gap`.
  - Optional `diagnostics` block for watcher stderr/timeouts.

### TUI Layout

1. **Header**: slice name, refreshed timestamp, active filters, refresh cadence.
2. **Table per flow** (rendered via `rich.Table`): columns `Flow`, `Latest Event`
   (with stage/surface), `Last Success (UTC) + Δmin`, `Errors/Alerts`, `Log`.
   - Rows with alerts use warning colors; stale success gaps (older than
     `--max-window`) are highlighted.
3. **Event Stream Pane** (optional, toggled via `j`/`JSON` hotkey): shows the
   last N JSON events emitted by watcher scripts if they support `--json`.
4. **Footer shortcuts**: `[r] refresh now`, `[f] filter flows`, `[q] quit`.

### JSON Stream Format

Each refresh writes a single line JSON object using the `SliceWatchSnapshot`
schema. Example:

```json
{
  "generated_at": "2026-03-22T10:15:00Z",
  "slice": "FEED-PERSONALIZED-DAILY",
  "flows": [
    {
      "flow_id": "feed",
      "label": "Personalized feed",
      "last_event": "feed.debug",
      "last_event_at": "2026-03-22T10:14:57Z",
      "last_success_at": "2026-03-22T10:14:57Z",
      "minutes_since_success": 0.05,
      "alerts": []
    }
  ],
  "summary": {
    "status": "healthy",
    "alert_count": 0,
    "oldest_success_gap_minutes": 0.05
  }
}
```

When `--json-stream -` is used without TUI (`watch json-stream`), the command
writes the same payload and exits, suitable for CI probes.

### Flow Definition & Config Schema

New top-level `watch.flows[]` block in `gracectl.yaml`:

```yaml
watch:
  flows:
    - id: feed
      label: Personalized feed
      script: python3 tools/log_watch/feed_admin_watch.py
      args:
        --feed-log: logs/feed.jsonl
        --admin-log: logs/admin.jsonl
        --window-minutes: 30
      surfaces: [feed.debug, feed.error]
      stale_after: 15m
      json_output: true
      multiplex: [feed, admin]
      slices: [FEED-PERSONALIZED-DAILY, ADMIN-ENTITLEMENTS-FLOW]
```

- `script`/`args` replace the current generic watcher commands so TUI can call
  them individually and parse JSON when supported.
- `surfaces` (optional) annotate stages shown in the TUI when scripts lack
  explicit fields.
- `stale_after` determines per-flow freshness thresholds; defaults to the
  top-level `--max-window`.
- `json_output: true` indicates the script supports `--json` or writes JSON to
  STDOUT (e.g., `tools/log_watch/forecast_catalog_watch.py`). If absent, the TUI
  falls back to parsing the summary text from STDOUT.
- `multiplex` lists logical flows returned by a single watcher (e.g.,
  `feed_admin_watch` emits both `feed` and `admin`). When provided, the runner
  dispatches the script once and splits the resulting statuses.
- `slices` restricts a flow to specific slice IDs; omit/empty list to reuse the
  flow globally.

### Integration with Existing Watchers

- `tools/log_watch/feed_admin_watch.py` already exposes structured `FlowStatus`
  dictionaries; extend it with `--json` to dump `{"flows": [...]}` for reuse by
  `multiplex` definitions.
- `tools/log_watch/forecast_catalog_watch.py` already imports helpers from
  `common.py`; it gains a `--json` flag mirroring the existing `FlowStatus.to_dict`.
- `gracectl.runners.logs.LogWatcherRunner` (new module) will:
  1. Resolve flow config from YAML / automation map defaults.
  2. Invoke each watcher command, capturing STDOUT/STDERR.
  3. Parse JSON responses when available; otherwise, wrap summary lines into
     alerts and set `log_path` for manual inspection.
- `watch tui` composes watchers asynchronously (via `asyncio` gather) so refresh
  intervals remain steady even if individual scripts take >5s.

### Result Storage & Alerts

- Every refresh writes a short-lived cache under
  `.gracectl/cache/watch/<slice>/<flow>.json` for other commands (e.g.,
  `gracectl slice verify --require-healthy-watch`).
- Alerts (non-empty `alerts[]`, stale success) trigger non-zero exit codes for
  `watch json-stream` invocations so CI fails fast.
- Failure packets (existing reporter) capture watcher STDERR when a script
  exits non-zero; packets are stored under `logs/gracectl/failures/watch/...`.

## Demo Personas & Evidence

### Persona Configuration

Augment `gracectl.yaml` slices with a `demo` block:

```yaml
demo:
  personas:
    - id: UC-FEED-DAILY
      title: Daily feed curation
      summary: "Showcase feed generation + admin alignment"
      script: scripts/demo/feed_daily.py
      env:
        USER_EMAIL: demo-feed@example.com
      steps:
        - type: backend
          checks: [backend.pipeline, pytest:tests/test_daily_feed_robustness.py]
        - type: ui
          command: ./scripts/run_e2e.sh e2e/core-ux.spec.ts -g "Daily feed"
        - type: replay
          command: python3 tools/feed_logs/replay_last.py --limit 100
        - type: evidence
          collect:
            - path: frontend/test-results/core-ux/*.png
              label: "Core UX screenshots"
            - path: logs/feed/*.jsonl
              label: "Feed log tail"
      report:
        template: docs/templates/demo_feed.md.j2
        output: docs/demo_reports/feed_daily.md
```

Key fields:

- `personas[]` is ordered; CLI defaults to the first persona when none given.
- `script` is optional—when present it can wrap custom automation (e.g., seed
  users) before/after generic steps.
- `steps` enforce typed stages so `gracectl demo` can show progress and map to
  reporters.
- `report.template` (Jinja2) allows narrative output; `output` path is where the
  rendered report plus evidence manifest go.

### CLI Commands

```
gracectl demo list [--slice <id>] [--config gracectl.yaml]
gracectl demo run <slice-id>
  [--persona UC-FEED-DAILY]
  [--fast]
  [--skip-backend] [--skip-frontend] [--skip-replay]
  [--evidence-dir logs/gracectl/demo]
  [--report-only]

gracectl demo record <slice-id>
  --persona <id>
  --output docs/demo_reports/<file>.md
  [--open-browser]
```

- `demo list` prints a table of personas per slice with summaries and required
  artifacts.
- `demo run` now orchestrates persona steps; legacy `--backend/--frontend` flags
  act as filters across the persona step list.
- `--report-only` re-renders the last recorded run using cached evidence
  (no checks executed) to update docs.
- `demo record` is a convenience alias for `demo run --report-only` followed by
  template rendering; `--open-browser` can preview the markdown via the default
  viewer.

### Execution Flow

1. **Env prep**: reuse `env_check` unless `--fast` is passed.
2. **Persona script hook**: if `scenario.script` exists, run it with provided
   environment variables; failure stops the demo.
3. **Step dispatcher**:
   - `backend` → call `slice_verify` backend runner with the referenced check
     IDs (mapped through `SliceRegistry`).
   - `ui` → shell out to Playwright commands; capture video/screenshot paths.
   - `replay` → call `slice_replay` flows or arbitrary commands.
   - `evidence` → glob the listed files and copy them into the evidence dir.
   - `note` (new optional type) → append static markdown to the report (e.g.,
     “Explain release gating context”).
4. **Evidence capture**: after each step, collect STDOUT/STDERR logs, artifacts
   (screenshots, JSON replays) into `logs/gracectl/demo/<slice>/<persona>/<ts>/`.
5. **Report generation**: assemble `DemoReport` dataclass:
   ```python
   @dataclass
   class DemoReport:
       slice: str
       persona_id: str
       run_started_at: datetime
       steps: list[DemoStepResult]
       evidence: list[EvidenceItem]
       summary: str
       status: Literal["passed", "failed", "skipped"]
       report_path: Path
   ```
   Render `report.template` (if provided) with this payload; otherwise, dump a
   default markdown summary inside the evidence directory.

### Evidence & Artifacts

- Directory layout: `logs/gracectl/demo/<slice>/<persona>/<ISO8601>/` containing:
  - `steps/<step-index>-<type>.json` (structured metadata + stdout paths).
  - `evidence/<label>/...` copies of screenshots/logs referenced in config.
  - `report.md` (rendered narrative) plus `report.json` (raw `DemoReport`).
- `reporter.write()` emits a `command="demo run"` entry referencing the
  evidence directory and summary status.
- When `--report-only` is used, the CLI loads the latest `report.json`, reruns
  the template, and writes a new markdown without executing steps.
- Provide `gracectl demo push-report <slice-id> --persona <id>` hook to copy the
  rendered report into `docs/` (per `report.output` path) and git-add friendly.

### Interactions with Automation Map

- `docs/GRACE_SLICE_AUTOMATION_MAP.md` remains the single source for mapping
  slices to backend/frontend commands. `gracectl demo` references those entries
  when persona steps omit explicit commands (e.g., `backend` step with only a
  `profile` name).
- Personas can cite automation map IDs via `ref: VM-FEED-ROBUSTNESS`; the CLI
  then auto-populates descriptive text inside the report to explain why each
  check matters.

## Code & API Changes

### New/Updated Modules

- `gracectl/commands/watch.py`
  - Add `tui`, `json_stream`, and `flows` subcommands.
  - Share an internal `WatchController` that loads configs, orchestrates runners,
    and streams snapshots to both TUI and reporters.

- `gracectl/runners/watch.py` *(new)*
  - Implements `LogWatcherRunner` with async `collect_flows(...)` returning
    `SliceWatchSnapshot` objects.
  - Handles multiplexed watchers, JSON parsing, and fallback text parsing.

- `gracectl/reporters/watch_stream.py` *(new)*
  - Writes `.jsonl` streams when `--json-stream` is active.
  - Persists `.gracectl/cache/watch/...` snapshots for reuse.

- `gracectl/config.py`
  - Extend schema with `watch.flows[]` and `demo.personas[]` keys.
  - Validate step types, CLI defaults, and `report.template` paths.

- `gracectl/commands/demo.py`
  - Add `list`, `record`, `push-report` subcommands.
  - Update `demo run` to dispatch persona steps and call new report renderer.

- `gracectl/demo.py` *(new helper)*
  - Houses `DemoPersona`, `DemoStep`, `DemoReport` dataclasses + execution logic.

### Types & JSON Contracts

Add to `gracectl/types.py`:

```python
@dataclass
class FlowStatus:
    flow_id: str
    label: str
    log_path: Path
    last_event: str | None
    last_event_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    alerts: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SliceWatchSnapshot:
    generated_at: datetime
    slice: str
    flows: list[FlowStatus]
    summary: WatchSummary

@dataclass
class DemoPersona:
    id: str
    title: str
    summary: str
    steps: list[DemoStep]
    report: DemoReportContract
```

Expose `gracectl watch --json` to print a serialized `SliceWatchSnapshot`. Keep
schemas backward compatible with `test-results/grace-report.json` entries.

## Adoption Plan

1. Extend watcher scripts with `--json` output & tests.
2. Implement `LogWatcherRunner` + new CLI subcommands; dogfood on
   `FEED-PERSONALIZED-DAILY` slice.
3. Add persona scaffolding for three flagship slices (feed, admin entitlements,
   forecast ladder) referencing `docs/GRACE_SLICE_AUTOMATION_MAP.md` evidence.
4. Document new YAML schema in `docs/gracectl.md` and add examples.
5. Hook `watch json-stream` into CI health checks and `demo push-report` into
   rollout notes scripts.

## Open Questions

1. Should the TUI persist acked alerts (e.g., hide until next failure)?
2. Do we need automatic Slack/webhook publishing from `--json-stream`? (Out of
   scope for MVP but interface enables it.)
3. Persona scripts may need secrets (e.g., demo accounts). Determine whether to
   load from `gracectl.local.yaml` overrides or env var references.
## Billing watcher integration

- Billing slice watchers in `gracectl watch` use `tools/log_watch/billing_watch.py` with JSON mode to capture `flow_id`, `correlation_id`, and severity codes. The YAML config now includes:
  ```yaml
  - id: FLOW-BILLING
    label: Billing & Credits
    script: PYTHONPATH=. python3 tools/log_watch/billing_watch.py
    args:
      --billing-log: logs/billing.jsonl
      --window-minutes: 20
    json_output: true
    stale_after: 30m
  ```
- CLI example: `PYTHONPATH=. python3 tools/log_watch/billing_watch.py --billing-log logs/billing.jsonl --window-minutes 20 --json` (exit 0-4 per severity). Add this flow to `gracectl watch tui FORECAST-LADDER-CATALOG-FLIP --flows FLOW-BILLING` to visualize billing freshness.
- The watcher JSON payload now includes a `block` field (set to `FLOW-BILLING`) so future TUIs can map alerts back to the configured row automatically.
- Cron snippet (place into `scripts/cron/watchers.cron` or systemd timer):
  ```cron
  */10 * * * * cd /opt/astro-project && PYTHONPATH=. python3 tools/log_watch/billing_watch.py --billing-log logs/billing.jsonl --window-minutes 20 --json >> logs/billing_watch.jsonl 2>&1
  ```
