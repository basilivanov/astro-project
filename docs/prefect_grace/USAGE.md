# Prefect GRACE Usage

## Terms

`Scaffold` means the initial frame of files, folders, contracts, and commands that later real automation will use. It is not the final non-stop system yet; it is the safe structure for building it.

## Create a feature

```bash
python3 -m prefect_grace.cli feature FEAT-EXAMPLE "Example Feature" "Business intent goes here"
```

## Create a packet

```bash
python3 -m prefect_grace.cli packet FEAT-EXAMPLE W01 "Backend logging packet" "Add strict logs to bounded backend flow" --role coder --reasoning high
```

## Record review and create rework

```bash
python3 -m prefect_grace.cli review FEAT-EXAMPLE-W01-BACKEND-LOGGING-PACKET rework_required --reason "Missing evidence" --create-rework
```

## Run Prefect flow locally

```bash
python3 -m prefect_grace.flows.feature_pipeline
```

## Run a test feature end-to-end

Safe dry-run:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DEMO "Demo Feature" "Validate Prefect + GRACE orchestration" --implementation-title "Demo Refactor Packet"
```

Real Codex execution:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DEMO "Demo Feature" "Validate Prefect + GRACE orchestration" --execute --timeout-seconds 3600
```

Real execution parses reviewer and architect wave verdicts from Codex output by default.
Verifier evidence is also parsed from Codex output by default.
For dry-run, `--reviewer-verdict` and `--wave-verdict` are fallback/simulation inputs because no real agent message exists.

Dry-run with simulated verifier blocker:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DEMO-VERIFY "Demo Verify" "Validate verifier routing" \
  --verifier-test-verdict failed \
  --verifier-observability-verdict no-evidence-blocker \
  --verifier-issue "No trace evidence recorded"
```

Real verifier runner with canonical repo commands:

```bash
python3 -m prefect_grace.cli test-feature FEAT-LIVE-VERIFY "Live Verify" "Run real verifier commands" \
  --execute \
  --touches-frontend \
  --observability-profile today-week \
  --artifact-glob "frontend/test-results/**/*" \
  --artifact-glob "artifacts/**/*"
```

Dry-run with forced reviewer rework:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DEMO-RW "Demo Rework" "Validate rework routing" --reviewer-verdict rework_required --review-reason "Missing log evidence"
```

Dry-run with architect escalation:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DEMO-ARCH "Demo Escalation" "Validate architect escalation" --reviewer-verdict escalate_to_architect --review-reason "Wrong packet decomposition"
```

What it does:
- creates `feature-brief.md` and `wave-plan.md`;
- seeds architect / planner / coder / verifier / reviewer / architect-wave-gate packets;
- runs them in strict order through the configured `codexN` wrapper;
- runs verifier as a real local runner, not a simulated Codex role;
- maps canonical backend/frontend/observability profiles to repo commands;
- injects dependency packet outputs into downstream prompts so reviewer/architect can consume prior evidence;
- records verifier evidence as a separate file-backed artifact;
- records reviewer verdict against the coder packet as a technical packet gate;
- runs an architect wave gate for business fit, UX fit, and frontend visual proof;
- creates a child rework packet or architect decision item when the verdict requires it;
- stores per-run artifacts under `prefect_grace/state/runs/`.

If `prefect` is not installed in the current Python environment, the same command still works in local fallback mode and preserves the same flow logic without Prefect UI/state features.

Current limitation:
- dry-run still uses CLI fallback verdicts unless `--parse-agent-output` is passed with prepared parseable output;
- verifier/reviewer/architect parsing currently expects the prompt contracts and markers from `prefect_grace/prompts/*.md`;
- verifier runner already executes canonical repo commands, but packet-specific targeting still needs richer planner/architect metadata.

## Intended next integration

The next implementation layer should replace stubs with real agent launchers:
- Architect xhigh prompt runner;
- Planner xhigh prompt runner;
- Coder runner through `codexN`/cliproxy;
- Verifier runner for backend/frontend/evidence profiles;
- Reviewer runner that consumes packet + diff + evidence.

## Run Codex for a packet through cliproxy

The launcher does not use Ductor. It runs a `codexN` wrapper such as `codex1`, which injects its own local `CODEX_HOME`, sends plain `gpt-5.4` to cliproxy, and lets cliproxy own routing/round-robin behind the API.
Do not pass profile-prefixed model names such as `codex-codex5/gpt-5.4`, and do not keep `CODEX_FORCE_PROFILE_MODEL_PREFIX=1`.

Config:

```bash
prefect_grace/agent_profiles.yaml
```

Dry-run:

```bash
python3 -m prefect_grace.cli run-codex FEAT-EXAMPLE-W01-BACKEND-LOGGING-PACKET --dry-run
```

Real run:

```bash
python3 -m prefect_grace.cli run-codex FEAT-EXAMPLE-W01-BACKEND-LOGGING-PACKET --timeout-seconds 3600
```

Run the real verifier directly:

```bash
python3 -m prefect_grace.cli run-verifier FEAT-EXAMPLE-W01-VERIFIER-EVIDENCE --timeout-seconds 3600
```

Effective subprocess shape:

```bash
codex1 exec -C /opt/astro-project -m gpt-5.4 ...
```

There is no separate live Prefect deployment for a single codex packet anymore.
Packet execution stays inside the canonical `prefect-grace-feature-pipeline` flow, while ad-hoc packet runs still use the CLI:

```bash
python3 -m prefect_grace.cli run-codex FEAT-EXAMPLE-W01-BACKEND-LOGGING-PACKET --dry-run
```

## Deploy live Prefect runs

Use the shared Prefect virtualenv because the project Python does not install Prefect by default:

```bash
# optional: create `prefect_grace/runtime.yaml` from the example and adjust
cp prefect_grace/runtime.yaml.example prefect_grace/runtime.yaml

PREFECT_API_URL=http://127.0.0.1:4200/api /opt/prefect/venv/bin/python -m prefect_grace.deploy_live
```

This creates or updates:
- `prefect-grace-feature-pipeline/live-feature-pipeline`
- `prefect-grace-packet-transition/live-packet-transition`
- `prefect-grace-review-router/live-review-router`
- `prefect-grace-live-dashboard/live-state-dashboard`

Rerunning deploy bootstrap only manages the canonical feature pipeline, packet transition, review router, and dashboard deployments.

The dashboard deployment is scheduled every 5 minutes and publishes a `grace-live-dashboard` artifact in the Prefect UI.

The deployment bootstrap reads runtime values from:

- `prefect_grace/runtime.yaml`
- or env overrides such as `PREFECT_GRACE_WORK_POOL`, `PREFECT_GRACE_LIVE_QUEUE`, `PREFECT_GRACE_WORKDIR`

Example dry-run submission through Prefect:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api /opt/prefect/venv/bin/prefect deployment run 'prefect-grace-feature-pipeline/live-feature-pipeline' \
  --params '{\"feature_id\":\"FEAT-PREFECT-LIVE-SMOKE\",\"title\":\"Prefect Live Smoke\",\"summary\":\"Validate live worker execution\",\"dry_run\":true,\"implementation_title\":\"Live Smoke Packet\",\"implementation_summary\":\"Run the full GRACE flow through the Prefect worker in dry-run mode.\"}'
```

## Operator queue

Print the YAML intake template:

```bash
python3 -m prefect_grace.cli print-brief-template
```

Submit a business feature brief into the local GRACE queue:

```bash
python3 -m prefect_grace.cli submit-brief path/to/feature-brief.yaml
```

Minimal brief contract:
- `feature_id`, `title`, `summary` are required.
- `scope`, `acceptance_criteria`, `non_goals`, and `visual_expectations` are folded into the generated feature brief and implementation packet summary.
- `verifier.*` selects backend/frontend/observability profiles and artifact globs.
- `touches_frontend` and `requires_frontend_visual` drive the visual verification gate.
- optional `planner_contract` lets the architect pre-seed exact waves and packets instead of relying on the default W01 contract.
- planner contract may contain multiple `waves` and arbitrary packet dependency chains; the pipeline now executes all packets, not only one static coder/verifier/reviewer chain.

Submit a feature into the local GRACE queue directly:

```bash
python3 -m prefect_grace.cli submit-feature FEAT-LIVE-DEMO "Live Demo" "Run a live Codex-backed feature" \
  --observability-profile read-only \
  --execute
```

Submit a canonical sequence of existing business features into the same live queue:

```bash
python3 -m prefect_grace.cli submit-sequence FEAT-ONE FEAT-TWO FEAT-THREE \
  --observability-profile read-only \
  --execute
```

Sequence behavior:
- reuses the same `prefect-grace-feature-pipeline/live-feature-pipeline` deployment;
- stores `sequence_id`, ordered `feature_ids`, and current index in `prefect_grace/state/job_queue.yaml`;
- only one feature from the sequence is dispatched at a time;
- later sequence items stay `pending` or `scheduled` until the previous feature reaches a terminal queue state;
- user-facing queue summaries stay in Russian: `Фича N/M`, `запланирована`, `в работе`, `ждёт коммита`, `заблокирована`, `Перехожу к следующей`.

Production-safe orchestration smoke in an isolated worktree:

```bash
python3 -m prefect_grace.cli submit-feature FEAT-PROD-CODEX-SMOKE "Prod Codex Smoke" "Real codex1 exec in isolated workdir" \
  --backend-profile grace_smoke \
  --observability-profile grace_smoke \
  --agent-workdir /tmp/prefect_grace_prod_worktree \
  --agent-sandbox danger-full-access \
  --execute
```

Inspect the queue:

```bash
python3 -m prefect_grace.cli queue
```

The queue output now includes both `jobs` and `sequences`, with Russian summaries for operator-facing sequence progress.

Render the operator dashboard:

```bash
python3 -m prefect_grace.cli dashboard
```

Dispatcher loop:

```bash
/opt/prefect/venv/bin/python -m prefect_grace.dispatcher --once
```

Behavior:
- serial dispatch only: a new queued feature is not submitted while another job is `dispatching`, `submitted`, or `running`;
- sequence dispatch is also serial within a batch: only the current `scheduled` item in a `sequence_id` can start;
- a feature line lock prevents the same `feature_id` from being dispatched in parallel by multiple queued entries;
- terminal job status is mapped from feature domain state, not only from Prefect run state;
- active live Codex packet writes logs into `prefect_grace/state/runs/<RUN_ID>/stdout.jsonl` and `stderr.log` during execution.
- Prefect run names are semantic: `feature:<FEATURE_ID>`, `packet:<PACKET_ID>`, `dashboard:grace-live`, instead of random animal names where our code controls naming.
- Prefect artifacts are visible in the UI `Artifacts` section; the monitoring flow now publishes both `grace-live-dashboard` and `grace-run-mapping`.
- planner-driven execution now supports:
  - multi-wave loop: `W01 -> W02 -> ...`;
  - all packets in a wave, ordered by dependencies;
  - auto-created reviewer rework bundles: `rework coder -> rework verifier -> rework reviewer`;
  - architect wave gates waiting for rework reviewer completion before final acceptance.

Dry-run example with an explicit planner contract:

```bash
python3 -m prefect_grace.cli test-feature FEAT-DYNAMIC "Dynamic Feature" "Exercise planner-driven execution" \
  --planner-contract '{"waves":[{"wave_id":"W01","title":"Wave 1","objective":"Backend","exit_conditions":["accepted"]},{"wave_id":"W02","title":"Wave 2","objective":"Frontend","exit_conditions":["accepted"]}],"packets":[{"key":"coder_backend","wave_id":"W01","title":"Backend Slice","role":"coder","reasoning":"high","summary":"Implement backend slice","dependencies":[]},{"key":"verifier_backend","wave_id":"W01","title":"Verify Backend Slice","role":"verifier","reasoning":"high","summary":"Verify backend slice","dependencies":["coder_backend"]},{"key":"reviewer_backend","wave_id":"W01","title":"Review Backend Slice","role":"reviewer","reasoning":"xhigh","summary":"Review backend slice","dependencies":["coder_backend","verifier_backend"]},{"key":"architect_backend","wave_id":"W01","title":"Architect Gate Backend","role":"architect","reasoning":"xhigh","summary":"Accept backend wave","dependencies":["reviewer_backend"]},{"key":"coder_frontend","wave_id":"W02","title":"Frontend Slice","role":"coder","reasoning":"high","summary":"Implement frontend slice","dependencies":["architect_backend"]},{"key":"verifier_frontend","wave_id":"W02","title":"Verify Frontend Slice","role":"verifier","reasoning":"high","summary":"Verify frontend slice","dependencies":["coder_frontend"]},{"key":"reviewer_frontend","wave_id":"W02","title":"Review Frontend Slice","role":"reviewer","reasoning":"xhigh","summary":"Review frontend slice","dependencies":["coder_frontend","verifier_frontend"]},{"key":"architect_frontend","wave_id":"W02","title":"Architect Gate Frontend","role":"architect","reasoning":"xhigh","summary":"Accept frontend wave","dependencies":["reviewer_frontend"]}]}' \
  --reviewer-verdict accepted \
  --wave-verdict accepted
```

Dry-run example for auto-rework:

```bash
python3 -m prefect_grace.cli test-feature FEAT-REWORK "Rework Feature" "Exercise auto rework loop" \
  --planner-contract '{"waves":[{"wave_id":"W01","title":"Wave 1","objective":"Single slice","exit_conditions":["accepted"]}],"packets":[{"key":"coder_main","wave_id":"W01","title":"Main Slice","role":"coder","reasoning":"high","summary":"Implement slice","dependencies":[]},{"key":"verifier_main","wave_id":"W01","title":"Verify Slice","role":"verifier","reasoning":"high","summary":"Verify slice","dependencies":["coder_main"]},{"key":"reviewer_main","wave_id":"W01","title":"Review Slice","role":"reviewer","reasoning":"xhigh","summary":"Review slice","dependencies":["coder_main","verifier_main"]},{"key":"architect_main","wave_id":"W01","title":"Architect Gate","role":"architect","reasoning":"xhigh","summary":"Accept wave","dependencies":["reviewer_main"]}]}' \
  --reviewer-verdict-script rework_required \
  --reviewer-verdict-script accepted \
  --review-reasons-script 'Fix boundary condition' \
  --wave-verdict-script accepted
```

Systemd unit template is provided in `systemd/prefect-grace-dispatcher.service`.
