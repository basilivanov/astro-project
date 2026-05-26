# Portable GRACE Orchestration Platform

> Текущая площадка разработки и отладки платформы: `/opt/astro-project`; целевая архитектура остаётся переносимой между проектами.

## Цель

Сделать не одноразовый оркестратор для `/opt/solarsage-astro`, а переносимую платформу, которую можно подключить к любому репозиторию и получить одинаковый цикл:

```text
grace/packets/*.md
  → backlog controller
  → Prefect runs
  → architect / planner / coder / verifier / reviewer / architect-gate
  → evidence / branch / commit / blocker
```

Пользователь должен иметь возможность положить в проект набор заранее продуманных GRACE controller packets, дать одну команду вечером, а утром увидеть:

- какие пакеты приняты;
- какие пакеты заблокированы;
- какие branch/worktree/commits созданы;
- какие evidence и diff scope были проверены;
- где именно остановился pipeline, если остановился;
- всё это в Prefect UI и в кратком Telegram summary.

## Главный принцип

Платформа не должна знать, что такое SolarSage, Astro, FastAPI, Next.js или конкретный бизнес-домен.

Платформа знает только:

- где лежит repo;
- где лежат GRACE packets;
- как запускать agents;
- как создавать isolated worktrees;
- как проверять scope;
- как запускать verification commands;
- как публиковать Prefect artifacts;
- как применять policy;
- как фиксировать результат.

Всё проектное подключается через конфиг и пакетные контракты.

## Не цели

- Не заменять Prefect своим scheduler/UI.
- Не заменять Codex/agy своим агентом.
- Не делать новую task queue поверх Prefect.
- Не требовать единого monorepo layout для всех проектов.
- Не писать бизнес-специфичную логику внутри platform core.
- Не обновлять исходные `grace/packets/*.md` на каждом run как runtime state.

## Целевая модель установки

### Platform layer

Отдельный переносимый Python package / repo:

```text
/opt/grace-orchestrator
  grace_orchestrator/
    cli.py
    config.py
    controller/
    packets/
    executors/
    prefect/
    verification/
    git/
    policies/
    artifacts/
    notifications/
```

Его можно подключить в проект одним из способов:

- `pip install -e /opt/grace-orchestrator`;
- git submodule;
- vendored copy на старте, с последующим выносом.

### Project layer

В каждом проекте лежит только проектная конфигурация и GRACE source-of-truth:

```text
project-root/
  grace/
    project.yaml
    development-plan.xml
    requirements.xml
    technology.xml
    knowledge-graph.xml
    verification-matrix.md
    packets/
      W-1.1.md
      W-1.1B.md
      W-1.2.md
    policies/
      executors.yaml
      rework.yaml
      merge.yaml
      verification.yaml
  docs/
    GRACE_CANON.md
```

Платформа читает эти файлы, но runtime state хранит отдельно.

### Runtime state layer

Mutable state не должен загрязнять проектный git tree.

Рекомендуемый layout:

```text
/var/lib/grace-orchestrator/<project_key>/
  state/
    packet_registry.yaml
    runs.yaml
    executor_history.yaml
    wave_status.yaml
  worktrees/
    <packet_id>/
  artifacts/
    <flow_run_id>/
```

На MVP можно хранить state в файлах. Позже можно заменить на SQLite/Postgres без изменения project packets.

Storage must be behind stable interfaces from day one:

```python
class PacketRegistryStore:
    def load_packet(packet_id: str) -> dict: ...
    def upsert_packet(packet: dict) -> None: ...
    def list_packets(project_key: str) -> list[dict]: ...

class RunStore:
    def create_run(record: dict) -> str: ...
    def update_run(run_id: str, patch: dict) -> None: ...

class ExecutorHistoryStore:
    def append_execution(record: dict) -> None: ...
```

MVP implementation may be YAML files. SQLite/Postgres implementation must not require changes in controller, executor, verifier, or packet parser code.

## Что остаётся в текущем проекте

Для `/opt/solarsage-astro` можно временно оставить существующий `prefect_grace/` как prototype, но новая архитектура должна постепенно вынести reusable код в `grace_orchestrator`.

Текущий `prefect_grace` уже содержит полезные части:

- role prompts;
- Codex launcher;
- Prefect feature pipeline;
- verifier/reviewer/architect parsing;
- Telegram notifications;
- dashboard artifact;
- file-backed state.

Но он пока смешивает:

- project-specific names;
- runtime state;
- packet generation workspace;
- Prefect deployment names;
- Codex-specific executor.

Цель переносимой платформы — разделить это на core и project adapter.

## Архитектурные слои

### 1. Project adapter

Отвечает за загрузку проектного конфига:

```yaml
project:
  key: solarsage-astro
  root: /opt/solarsage-astro
  default_branch: main
  grace_dir: grace
  packets_dir: grace/packets
  canon_doc: docs/GRACE_CANON.md

prefect:
  api_url: http://127.0.0.1:4200/api
  public_ui_url: https://prefect.vasiliy-ivanov.ru
  work_pool: solarsage-astro-process
  live_queue: solarsage-astro-live
  monitoring_queue: solarsage-astro-monitoring
  concurrency_limit: 1

runtime:
  state_root: /var/lib/grace-orchestrator/solarsage-astro
  artifact_root: /var/lib/grace-orchestrator/solarsage-astro/artifacts
  worktree_root: /var/lib/grace-orchestrator/solarsage-astro/worktrees
```

Платформа не должна иметь hardcoded `/opt/solarsage-astro`.

### 2. Packet scanner/parser

Читает `grace/packets/*.md` и строит typed model `ControllerPacket`.

Минимальные поля:

```yaml
packet_id: W-1.2
status: ready
phase: PHASE-1-MOCKED-PIPELINE
wave: W-1.2
modules:
  - M-AUTH-TG
  - M-PROFILE
depends_on:
  - W-1.1
  - W-1.1B
```

Если `depends_on` отсутствует, MVP может вывести зависимости из порядка `phase + wave`, но платформа должна предупреждать, что implicit dependencies менее надёжны.

Из Markdown дополнительно извлекаются:

- `Goal`;
- `Allowed Write Scope`;
- `Frozen / Out Of Scope`;
- `Must Preserve`;
- `Verification`;
- `Expected Evidence`;
- `Escalation triggers`;
- `Decision`;
- `Evidence`;
- `Reviewer notes`.

Parser не должен быть LLM-based. Это deterministic слой.

#### Markdown schema contract

Parser должен ожидать фиксированную Markdown-схему, а не "примерный текст".

Минимально допустимый controller packet:

```markdown
# Controller Packet — W-1.2: Telegram auth + users

status: ready
phase: PHASE-1-MOCKED-PIPELINE
wave: W-1.2
modules: M-AUTH-TG · M-PROFILE
depends_on:
  - W-1.1
  - W-1.1B

---

## Goal

## Allowed Write Scope

## Frozen / Out Of Scope

## Must Preserve

## Verification

## Expected Evidence

## Escalation triggers

## Decision

## Evidence

## Reviewer notes
```

Rules:

- front matter may be YAML or simple `key: value` lines before the first `---`;
- section names are case-sensitive in MVP;
- missing required runtime sections produce `packet_schema_invalid`;
- unknown sections are allowed only under `## Notes` or `## Appendix`;
- parser records source line numbers for every section.

Validation error shape:

```json
{
  "error_code": "packet_schema_invalid",
  "packet_path": "grace/packets/W-1.2.md",
  "line": 42,
  "section": "Verification",
  "message": "Missing required section: ## Verification"
}
```

Schema errors are published as Prefect artifacts and Telegram blockers. They do not start agent execution.

### 3. Packet registry

Хранит runtime-состояние независимо от source packet:

```yaml
packets:
  W-1.2:
    source_path: grace/packets/W-1.2.md
    source_hash: sha256:...
    status: queued|running|accepted|blocked|superseded
    phase: PHASE-1-MOCKED-PIPELINE
    wave: W-1.2
    dependencies:
      - W-1.1
      - W-1.1B
    latest_flow_run_id: ...
    latest_branch: agent/W-1.2
    attempts: 1
    rework_count: 0
    executor_history:
      - role: coder
        executor: codex
        attempt: 1
```

Idempotency:

- если packet hash не менялся и статус `accepted`, повторно не запускать;
- если packet hash изменился после accepted — пометить `changed_after_acceptance` и требовать явного `--rerun-changed`;
- если статус `blocked`, повторно запускать только с `--retry-blocked` или после изменения packet hash;
- Prefect idempotency key должен включать `project_key + packet_id + source_hash`.

#### Source hash normalization

`source_hash` должен считаться не по всему файлу, а по canonical execution contract.

В hash входят:

- front matter keys that affect execution: `status`, `phase`, `wave`, `modules`, `depends_on`, `planner_required`, executor hints;
- `Goal`;
- `Allowed Write Scope`;
- `Frozen / Out Of Scope`;
- `Must Preserve`;
- `Verification`;
- `Expected Evidence`;
- `Escalation triggers`;
- `Decision`, only if it changes implementation semantics.

В hash не входят:

- `Evidence`;
- `Reviewer notes`;
- runtime comments;
- timestamps;
- generated Prefect links;
- final acceptance appendices.

Это нужно, чтобы добавление evidence/review notes не вызывало вечный rerun уже принятого packet.

### 4. Backlog controller

Главный runtime-flow.

Команды:

```bash
grace-orchestrator sync-packets --project /opt/solarsage-astro --dry-run
grace-orchestrator submit-packets --project /opt/solarsage-astro --execute
grace-orchestrator run-nightly --project /opt/solarsage-astro --until-blocked
```

Поведение:

1. Acquires project runtime lock.
   - lock path: `<state_root>/locks/backlog-controller.lock`;
   - second nightly run exits with `controller_already_running`;
   - stale lock detection is based on PID/process heartbeat and max lock age.
2. Сканирует `grace/packets`.
3. Валидирует packet format.
   - schema errors stop the affected packet before agent execution;
   - global parse failures stop the whole backlog run.
4. Обновляет registry.
   - computes normalized `source_hash`;
   - preserves accepted packets with same hash;
   - marks changed accepted packets as `changed_after_acceptance`;
   - marks changed blocked packets as `ready_for_retry`.
5. Строит DAG.
   - dependencies come from explicit `depends_on`;
   - implicit wave ordering is allowed only as MVP fallback and emits warning;
   - cycles produce `dependency_cycle_blocker` and stop the run.
6. Выбирает ready packets:
   - `status: ready`;
   - все dependencies accepted;
   - packet не accepted раньше с тем же hash;
   - нет активного conflicting packet.
7. Cascading dependency rules:
   - if a dependency becomes `blocked`, dependent packets become `cascading_blocked`;
   - cascading packets are not executed until dependency is accepted or packet dependencies change.
8. Создаёт Prefect flow runs.
9. Соблюдает project concurrency.
10. Останавливается на blocker, если policy требует fail-fast.

#### DAG validation output

Backlog controller must publish a machine-readable DAG artifact:

```json
{
  "project_key": "astro-project",
  "packets_total": 20,
  "ready": ["W-1.1"],
  "accepted": [],
  "blocked": [],
  "cascading_blocked": [],
  "cycles": [],
  "warnings": []
}
```

The same data should also be rendered as a concise Markdown table in Prefect UI.

### 5. Prefect runtime

Prefect остаётся операционным runtime:

- queue;
- scheduled runs;
- retries;
- task logs;
- artifacts;
- UI;
- deployments;
- concurrency limits.

Минимальные flows:

```text
grace-backlog-controller
grace-packet-runner
grace-dashboard
grace-packet-transition
```

Для каждого project deployment names должны иметь prefix:

```text
<project_key>-backlog-controller
<project_key>-packet-runner
<project_key>-dashboard
```

Prefect tags:

```text
project:<project_key>
phase:<phase_id>
wave:<wave_id>
packet:<packet_id>
role:<role>
executor:<executor>
```

#### Workflow runtime adapter

Prefect is the first workflow runtime, not a permanent hard dependency of the domain controller.

Platform core must call a runtime adapter:

```python
class WorkflowRuntime:
    name: str

    def submit_packet_run(packet: ControllerPacket, parameters: dict) -> WorkflowRunRef: ...
    def submit_backlog_run(project: ProjectConfig, parameters: dict) -> WorkflowRunRef: ...
    def publish_artifact(run_ref: WorkflowRunRef, name: str, body: str | dict) -> None: ...
    def read_run_status(run_ref: WorkflowRunRef) -> dict: ...
```

MVP runtime:

```yaml
workflow_runtime:
  type: prefect
```

Future runtime options may include `temporal`, `github_actions`, or a local process runner. Controller semantics must not depend on Prefect-specific objects outside the Prefect adapter.

#### Why Prefect v1 runtime is still acceptable

Prefect is intentionally used as an operating plane:

- queue and scheduling;
- UI for long-running LLM jobs;
- retries/timeouts;
- artifacts;
- operator dashboard.

It is not the GRACE brain. Agent decisions, packet status, scope guard, verification, and merge policy remain in platform code and project state. If Prefect becomes too heavy, replacing only `WorkflowRuntime` should be possible.

### 6. Worktree manager

Каждый packet выполняется не в основном repo, а в isolated worktree.

Branch naming:

```text
agent/<project_key>/<packet_id>/<attempt>
```

Алгоритм:

1. Fetch/update base branch.
2. Create worktree from clean base.
3. Copy/resolve project config.
4. Run packet lifecycle inside worktree.
5. Verify diff scope.
6. If accepted, merge/squash into integration branch or main according to policy.
7. Preserve worktree on blocker for inspection.
8. Prune accepted worktrees after retention period.

На старте можно делать simpler mode без worktrees, но platform API сразу должен иметь `worktree_strategy`.

```yaml
git:
  worktree_strategy: per_packet
  merge_strategy: squash_after_acceptance
  keep_failed_worktrees: true
  auto_push: false
```

### 7. Executor registry

Платформа запускает не `codex`, а abstract executor.

Интерфейс:

```python
class AgentExecutor:
    name: str

    def run(packet: AgentPacket, context: AgentContext) -> AgentRunResult:
        ...
```

Единый результат:

```json
{
  "packet_id": "W-1.2",
  "role": "coder",
  "executor": "codex",
  "attempt": 1,
  "returncode": 0,
  "stdout_path": "...",
  "stderr_path": "...",
  "last_message_path": "...",
  "final_markers": {},
  "changed_files": [],
  "evidence_paths": []
}
```

Stable executor input contract:

```json
{
  "project": {"key": "...", "root": "..."},
  "packet": {"packet_id": "...", "source_path": "...", "source_hash": "..."},
  "role": "coder",
  "attempt": 1,
  "worktree": {"path": "...", "branch": "..."},
  "context_paths": [],
  "policy": {},
  "timeout_seconds": 3600
}
```

Executor errors must use stable categories:

- `executor_start_failed`;
- `executor_timeout`;
- `executor_stalled`;
- `executor_output_parse_error`;
- `executor_returncode_failed`;
- `executor_contract_violation`.

Reviewer/verifier/merge code must consume `AgentRunResult`, not executor-specific stdout.

MVP executors:

- `codex`;
- `agy` placeholder/adapter;
- `manual` placeholder for human step.

Policy:

```yaml
executors:
  architect:
    priority: [codex]
    reasoning: xhigh
    resume: feature_role
  planner:
    priority: [codex]
    reasoning: xhigh
    resume: feature_role
  coder:
    priority: [codex, agy]
    fallback: codex
    reasoning: high
  verifier:
    priority: [codex]
    reasoning: medium
  reviewer:
    priority: [codex]
    reasoning: xhigh
    resume: feature_role
```

### 8. Architect preflight

Перед кодингом architect получает source controller packet и решает:

```json
{
  "decision": "execute_as_is | split_required | needs_user_decision | reject_packet",
  "reason": "...",
  "child_packets": [],
  "required_canon_updates": [],
  "risk_level": "low|medium|high"
}
```

Правило:

- если packet уже atomic и содержит строгий `Allowed Write Scope` + `Verification`, planner не обязателен;
- если packet большой или scope неатомарный, architect может включить planner;
- если packet требует изменения канона, сначала отдельная canon-update lane;
- если frozen scope нарушен, blocker до user/controller decision.

Это важно: готовые controller packets не надо заново нарезать всегда. Planner — не default tax, а инструмент для split/rework.

### 9. Planner optional mode

Planner запускается только если:

- architect вернул `split_required`;
- packet явно содержит `planner_required: true`;
- rework требует decomposition;
- DAG содержит multi-packet wave without explicit child packet graph.

Planner output должен быть machine-readable:

```json
{
  "waves": [...],
  "packets": [...]
}
```

Но для source controller packets MVP может использовать direct execution path.

### 10. Scope guard

Scope guard обязательный и deterministic.

Input:

- `Allowed Write Scope`;
- `Frozen / Out Of Scope`;
- actual `git diff --name-only`.

Output:

```json
{
  "verdict": "pass|fail",
  "allowed_changed_files": [],
  "blocked_changed_files": [],
  "frozen_violations": []
}
```

Правила:

- exact path match разрешён;
- directory pattern разрешён только если packet явно указал `dir/**`;
- deletion allowed только если packet явно разрешает deletion/drift cleanup;
- generated files должны быть либо в scope, либо listed as generated artifacts;
- violation автоматически переводит packet в `blocked_scope_violation`;
- coder не получает шанс “объяснить” scope violation как accepted без architect decision.

### 11. Verification runner

Verifier может быть LLM-agent, но execution commands должны быть deterministic.

Источник команд:

- section `Verification`;
- project `grace/policies/verification.yaml`;
- packet overrides.

Пример:

```yaml
profiles:
  api_quick:
    working_dir: apps/api
    commands:
      - ruff check .
      - mypy app
      - pytest -q
  contracts_check:
    working_dir: .
    commands:
      - pnpm contracts:generate
      - git diff --exit-code -- packages/contracts/openapi.json packages/contracts/_generated.ts
```

Verifier обязан вернуть:

- commands run;
- exit codes;
- stdout/stderr paths;
- evidence paths;
- scope guard result;
- final verdict.

Stable verifier output contract:

```json
{
  "packet_id": "W-1.2",
  "verdict": "passed|failed|blocked",
  "commands": [
    {"cmd": "pytest -q", "cwd": "apps/api", "exit_code": 0, "stdout_path": "...", "stderr_path": "..."}
  ],
  "scope_guard": {"verdict": "pass", "violations": []},
  "evidence_paths": [],
  "blocking_issues": [],
  "metrics": {"duration_seconds": 12.3}
}
```

LLM-verifier может дополнительно интерпретировать logs, но не должен заменять command execution.

### 12. Review lifecycle

Lifecycle одного source packet:

```text
source packet ready
  → architect preflight
  → optional planner split
  → coder
  → scope guard
  → verifier
  → reviewer
  → architect packet/wave gate
  → merge steward
  → accepted / blocked / rework
```

Если reviewer не принял:

- `quality_rework`: вернуть coder;
- `scope_violation`: architect decision;
- `verification_missing`: verifier/pipeline rework;
- `environment_blocker`: stop or infrastructure retry;
- `canon_conflict`: architect/planner/canon lane.

### 13. Rework/executor policy

Policy-файл:

```yaml
rework:
  max_total_attempts_per_packet: 3
  same_executor_rework_limit: 1
  switch_coder_after_quality_reworks: 2
  architect_escalation_after_total_reworks: 3
  environment_retry_limit: 1
```

Пример поведения:

1. Coder `codex` сделал packet.
2. Reviewer вернул `rework_required`.
3. Первый rework — resume same coder/executor.
4. Второй quality rework — rotate coder to next executor, например `agy`.
5. Третий rework — architect escalation.

Не менять coder при:

- environment blocker;
- missing dependency;
- failing infra command;
- bad packet contract;
- frozen scope conflict.

#### Rework loop detail

One packet attempt has strict phases:

```text
coder
  → scope guard
  → deterministic verification commands
  → verifier evidence summary
  → reviewer verdict
  → architect gate
```

If deterministic verification fails:

- create `rework_evidence.md`;
- classify blocker as `failed_verification`;
- increment `rework_count`;
- if below limit, return to coder with only packet context + verification evidence;
- if over limit, mark packet `blocked`.

If reviewer fails the packet:

- create `review_comments.md`;
- classify blocker;
- increment `rework_count` only for `quality_rework`;
- route scope/canon/environment failures to the responsible lane instead of blindly returning to coder.

Every rework must preserve:

- original packet intent;
- allowed/frozen scope;
- dependency context;
- previous verifier/reviewer evidence.

### 14. Merge steward

Merge steward не должен быть LLM.

Responsibilities:

- ensure clean worktree;
- rebase packet branch onto latest merge target before final acceptance;
- run final verification;
- enforce scope guard;
- squash commit with generated message;
- optionally push;
- update registry;
- publish Prefect artifacts.

Merge policy:

```yaml
merge:
  target_branch: main
  integration_branch: grace/integration
  before_merge: rebase_onto_target
  final_verification_required: true
  conflict_policy: block_and_preserve_worktree
  strategy: squash_after_acceptance
```

If rebase/merge conflicts happen:

- packet status becomes `blocked`;
- blocker category is `merge_conflict`;
- worktree and branch are preserved;
- no auto-resolution by LLM unless controller explicitly launches a conflict-resolution packet;
- dependent packets become `cascading_blocked`.

Commit message format:

```text
grace(<packet_id>): <packet title>

Phase: <phase>
Wave: <wave>
Executor: <executor>
Prefect-Run: <flow_run_id>
Evidence: <artifact_uri>
```

For blocked runs:

- no merge;
- worktree preserved;
- diff artifact saved;
- blocker summary sent to Telegram.

### 15. Artifacts

Every packet run must publish:

- source packet path/hash;
- Prefect run mapping;
- agent runs per role;
- branch/worktree path;
- diff stat;
- changed files;
- scope guard result;
- verification command outputs;
- reviewer verdict;
- architect gate verdict;
- merge/commit result;
- blocker summary if any.

Prefect artifacts should include a human-readable Markdown table:

```text
packet_id | phase | wave | status | executor | branch | commit | evidence
```

Nightly flow artifact should additionally include:

- Mermaid DAG with accepted/blocked/pending states;
- diff stat per accepted packet;
- failed command summary per blocked packet;
- links to worktree/branch/commit;
- executor rotation history.

### 16. Notifications

Telegram should send only major events:

- nightly started;
- packet accepted;
- packet blocked;
- phase completed;
- executor rotated;
- merge conflict;
- nightly summary.

Do not send every task heartbeat.

Nightly summary format:

```text
🤖 GRACE Nightly: <project_key>
Flow: <prefect_run_url>

✅ ACCEPTED (<n>)
• W-1.1 — <title> — <commit>

🚫 BLOCKED (<n>)
• W-1.3 — <title>
  Reason: <category>, attempt <x>/<max>
  Branch: <branch>

⏳ PENDING / CASCADING (<n>)
• W-1.4 — depends on W-1.3
```

Telegram payload must be short enough to scan in under 10 seconds. Full evidence belongs in Prefect artifacts, not Telegram.

### 17. Security/secrets

Платформа не должна копировать `.env` в artifacts.

Rules:

- env values redacted by key pattern;
- no raw tokens in prompts;
- agents receive only paths and allowed commands;
- worktrees use project-local `.env` only if policy allows;
- external executors must be explicitly trusted per project.

Verification isolation policy:

```yaml
verification_runtime:
  mode: host|docker|project_venv
  default: project_venv
  allow_host_commands: false
  docker_image: null
```

MVP may run on host for trusted local projects, but the platform contract must support isolated verification because worktrees are not a security boundary.

#### Secret scanning gate

Before merge steward can accept a packet, the platform must run a secret scan on:

- `git diff`;
- newly created files;
- generated artifacts that may be committed.

MVP can use a lightweight regex scanner. Production can switch to `gitleaks`, `detect-secrets`, or GitHub secret scanning.

Secret scan result:

```json
{
  "verdict": "pass|fail",
  "findings": [
    {"path": "file", "line": 10, "rule": "possible_api_key", "redacted_sample": "sk-..."}
  ]
}
```

Any positive finding blocks merge until manually waived by controller policy.

#### Least-privilege branch policy

Agent branches/worktrees must have minimum operational rights:

- no direct push to protected branches;
- no automatic force-push unless explicitly enabled per project;
- merge to target branch only through merge steward;
- external executors get an allowlist of env vars and commands;
- destructive commands require explicit project policy approval.

### 18. CI/CD integration

The platform behaves like a local CI/CD layer, so it must not fight external CI.

Rules:

- Local GRACE verification gates run before merge/push.
- External CI, such as GitHub Actions, remains an independent final gate after push/PR.
- If external CI fails, packet or phase status becomes `external_ci_failed`.
- The platform must not disable or bypass required branch protection checks.
- `auto_push` must default to `false` until a project explicitly opts in.
- GitHub Actions jobs triggered by agent pushes should be linked back into Prefect artifacts when possible.

CI policy:

```yaml
external_ci:
  enabled: true
  provider: github_actions
  wait_for_checks: false
  fail_status: external_ci_failed
  required_checks: []
```

MVP can record the pushed commit URL only. Later versions can poll GitHub check-runs and update registry.

### 19. Operational observability

Artifacts and Telegram are enough for debugging, but operations need metrics.

MVP metrics can be emitted as JSON artifacts and appended to runtime state. Later they can be exported to Prometheus/StatsD/OpenTelemetry.

Required metric names:

```text
grace_packet_duration_seconds
grace_packet_ready_to_terminal_seconds
grace_packets_accepted_total
grace_packets_blocked_total
grace_packets_failed_total
grace_rework_total
grace_rework_by_reason_total
grace_executor_runs_total
grace_executor_failures_total
grace_executor_rotation_total
grace_scope_violations_total
grace_verification_failures_total
grace_merge_conflicts_total
grace_external_ci_failures_total
```

Every terminal packet run must record:

- ready timestamp;
- start timestamp;
- terminal timestamp;
- terminal status;
- blocker category if any;
- executor attempts;
- rework count;
- verification duration;
- merge duration.

### 20. CLI and machine-readable output

Every CLI command must support human output and `--json`.

Required commands:

```bash
grace-orchestrator validate-project --project /path --json
grace-orchestrator sync-packets --project /path --dry-run --json
grace-orchestrator submit-packets --project /path --execute --json
grace-orchestrator run-nightly --project /path --until-blocked --json
grace-orchestrator packet-status --project /path --packet-id W-1.2 --json
grace-orchestrator registry-dump --project /path --json
```

JSON response envelope:

```json
{
  "ok": true,
  "project_key": "astro-project",
  "command": "sync-packets",
  "result": {},
  "errors": [],
  "warnings": []
}
```

Non-zero exit codes:

- `1` validation/runtime error;
- `2` packet schema invalid;
- `3` dependency/DAG invalid;
- `4` external runtime unavailable;
- `5` security/scope violation.

### 21. Portability contract

Чтобы подключить новый проект, нужны только:

1. repo path;
2. `grace/project.yaml`;
3. `grace/packets/*.md`;
4. verification profiles;
5. executor policy;
6. Prefect work pool/queue;
7. optional Telegram settings.

Нельзя требовать:

- конкретный backend stack;
- конкретный frontend stack;
- конкретные test commands;
- наличие Docker;
- наличие Next/FastAPI;
- старый `/opt/astro-project` layout.

## MVP implementation plan

### MVP-1: Project GRACE layout

Deliverables:

- create `grace/` layout in `/opt/solarsage-astro`;
- add `grace/project.yaml`;
- add `grace/policies/*.yaml`;
- define packet naming and dependency conventions.

Acceptance:

- `grace-orchestrator validate-project /opt/solarsage-astro` passes.

### MVP-2: Packet parser + registry

Deliverables:

- deterministic Markdown parser;
- source hash;
- registry state;
- dry-run sync.

Acceptance:

```bash
grace-orchestrator sync-packets --project /opt/solarsage-astro --dry-run
```

prints ordered packets and dependency status.

### MVP-3: Prefect backlog controller

Deliverables:

- `backlog-controller` flow;
- `packet-runner` flow;
- project-specific deployment generator;
- tags/artifacts.

Acceptance:

- one ready packet creates one Prefect run;
- accepted packet is not resubmitted with same hash.

### MVP-4: Executor registry

Deliverables:

- `codex` executor adapter using existing Codex launcher logic;
- `agy` placeholder adapter;
- executor policy reader;
- executor history in registry.

Acceptance:

- coder executor can be switched by config without changing pipeline code.

### MVP-5: Worktree + scope guard

Deliverables:

- per-packet worktree;
- branch naming;
- changed-file extraction;
- allowed/frozen scope validation.

Acceptance:

- packet that changes frozen file is blocked before merge.

### MVP-6: Verification + reviewer/architect gates

Deliverables:

- deterministic command runner;
- verifier artifact;
- reviewer prompt context;
- architect final gate;
- blocker classification.

Acceptance:

- W-1.1-like packet can run end-to-end to accepted with evidence.

### MVP-7: Rework policy + executor rotation

Deliverables:

- rework counters;
- quality/environment/canon/scope blocker taxonomy;
- switch coder after configured rework count;
- Prefect artifact explaining rotation.
- source-hash resume gate:
  - if `EXECUTION_PACKET.md` source contract changes, previous coder session is stale;
  - changed `source_hash` forbids `light_resume`;
  - managed resume must not fail open on registry corruption;
  - launcher must force fresh execution when registry says `resume_allowed=false`.

Acceptance:

- simulated two quality reworks rotate coder from `codex` to `agy` or fallback executor.
- changed source contract never produces `codex resume`.
- same source contract plus reviewer-only small fix may resume only when a valid coder session exists.

### MVP-7B: Synthetic edge matrix

Deliverables:

- generated synthetic scenario matrix;
- named invariants for source hash, resume, registry, dependency, scope, and artifact edge cases;
- fast `smoke` matrix for PR checks;
- larger deterministic `full` matrix for nightly/local stress.

Acceptance:

- matrix proves `source_hash_changed -> no resume command ever`;
- matrix proves `resume_allowed=false -> fresh exec`;
- matrix proves registry error on managed light-resume cannot silently reuse an old thread;
- no live Codex/Claude/agy/Prefect/Product services are started by matrix tests.

### MVP-7C: Large module split sequence

Large-file refactors must happen only after MVP-7 and MVP-7B are accepted.

Order:

1. `feature_pipeline.py` split;
2. `codex_launcher.py` split.

Rules:

- these are extraction-only packets;
- no behavior changes are allowed inside module-split packets;
- synthetic edge matrix must remain green before and after each split;
- `codex_launcher.py` must not be split while a source-hash resume gate rework is still open.

### MVP-8: Merge steward + nightly mode

Deliverables:

- squash merge after accepted;
- optional push;
- nightly summary;
- stop-on-blocker / continue-independent policy.

Acceptance:

```bash
grace-orchestrator run-nightly --project /opt/solarsage-astro --until-blocked
```

runs ready packets in order, merges accepted work, stops with clear blocker if needed.

## Key implementation decisions

### Decision 1: Source packets are immutable during run

Do not write runtime evidence into `grace/packets/W-*.md` during execution.

Reason:

- source packet is the controller contract;
- runtime state belongs to Prefect/state/artifacts;
- mutating packet files causes noisy diffs and makes scope guard harder.

If desired, a final signed evidence appendix can be written by an explicit `finalize-docs` lane.

### Decision 2: Prefect is runtime, not domain brain

Prefect stores runs, tasks, logs, artifacts, schedules.

GRACE decisions remain in:

- packets;
- platform state;
- agent outputs;
- reviewer/architect verdicts.

### Decision 3: Planner is optional for ready controller packets

If a packet already has strict scope and verification, architect can approve direct execution.

Planner runs when decomposition is needed.

### Decision 4: Executors are plugins

The platform calls `run_agent(role, executor, packet, context)`, not `run_codex`.

Codex is default executor, not the platform.

### Decision 5: Verification commands are deterministic

LLM can review logs, but tests and scope checks are deterministic command runs.

### Decision 6: Safety gate before large-file refactor

The orchestrator must not refactor large runtime modules before the source-hash
resume gate and synthetic edge matrix are accepted.

Rationale:

- large refactors increase rework probability;
- stale resume during refactor can continue from an obsolete contract;
- synthetic invariants are the cheapest way to prove behavior preservation;
- keeping safety gates separate from module splits makes reviewer verdicts
  defensible.

Required sequence:

```text
FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP
  -> FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP
  -> FEAT-GRACE-FEATURE-PIPELINE-MODULE-SPLIT
  -> FEAT-GRACE-CODEX-LAUNCHER-MODULE-SPLIT
```

## Acceptance criteria for the portable platform

The platform is considered portable when:

- a second repo can be onboarded by adding only `grace/project.yaml`, packets, and policies;
- no Python code changes are required for a new project;
- Prefect deployments are generated from project config;
- executor choice is config-driven;
- verification profiles are config-driven;
- all project-specific paths are outside platform code;
- packet parser accepts the same controller packet style across projects;
- a source packet can run to accepted/blocker with artifacts visible in Prefect.

## Open questions

These are implementation choices, not blockers:

- state backend MVP: YAML files vs SQLite;
- merge target: main directly vs integration branch;
- whether accepted run evidence should ever be committed;
- how much of existing `prefect_grace` is migrated vs wrapped first;
- exact `agy` command-line contract.

Recommended defaults:

- YAML state first;
- per-packet worktree;
- squash merge into current branch only after architect gate;
- no auto-push until stable;
- Codex executor first, `agy` adapter second.
