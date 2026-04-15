# Prefect × Strict GRACE Blueprint

## Goal

Build a non-stop agent pipeline where:

- the Architect thinks in business features;
- an Architect agent formalizes the feature into GRACE artifacts;
- a Planner slices the work into waves and packets;
- Coder agents implement packets with different reasoning levels;
- QA/Reviewer agents validate tests, logs, traces, and UI evidence;
- Prefect orchestrates retries, state transitions, and observability.

This blueprint is intentionally file-backed first. No database is required for phase 1.

## Phase 1 Operating Model

### Human role

The human Architect:
- defines business intent;
- approves architecture-level decisions;
- decides whether rejected work should be reworked, split, deferred, or escalated;
- is the final acceptance authority for a feature unless explicitly delegated.

### Agent roles

#### 1. Architect Agent
Responsible for translating feature intent into GRACE artifacts.

Outputs:
- feature packet directory;
- updates to `requirements.xml` if scope/invariants change;
- updates to `technology.xml` if runtime/tooling changes;
- updates to `development-plan.xml` if execution topology changes;
- updates to `knowledge-graph.xml` for impacted modules/flows/contracts;
- updates to `verification-matrix.md` for new or changed verification lanes;
- feature-local packet docs for the execution wave.

#### 2. Planner Agent
Responsible for decomposition.

Outputs:
- wave list;
- packet list;
- ownership map;
- packet dependencies;
- acceptance gates;
- model/reasoning assignment per packet.

#### 3. Coder Agent
Responsible for implementing one packet inside a bounded write scope.

Outputs:
- code changes;
- packet status update;
- implementation note;
- targeted verification result references.

#### 4. Reviewer Agent
Responsible for packet-level technical acceptance or rejection.

Outputs:
- review verdict: `accepted`, `rework_required`, `blocked`, `escalate_to_architect`;
- blocker notes;
- suggested follow-up packet delta if rejection is remediable.

#### 5. Verifier Agent
Responsible for running the required test profile and post-test observability review.

Outputs:
- test verdict;
- evidence paths;
- observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, `no-evidence-blocker`.

## What is a Plan Artifact?

A plan artifact is not “just a todo list”.

In this system, a plan artifact is the execution contract that connects:
- feature intent;
- impacted modules;
- allowed write scopes;
- wave order;
- verification gates;
- ownership.

At project level this is mainly `development-plan.xml`.
At feature level this becomes a feature packet bundle, for example:

- `docs/prefect_grace/features/FEAT-XXX/feature-brief.md`
- `docs/prefect_grace/features/FEAT-XXX/wave-plan.md`
- `docs/prefect_grace/features/FEAT-XXX/packets/PACKET-001.md`

So yes: the Architect agent prepares plan artifacts, but it does so by updating and extending the existing GRACE documents, not by recreating the whole GRACE corpus on every wave.

## How Architect manages GRACE

The Architect agent does **incremental GRACE maintenance**.

It does **not** create a fresh knowledge graph or verification matrix for every wave.
Instead it:

1. reads the current project GRACE baseline;
2. identifies impacted nodes/flows/contracts;
3. appends or patches only the affected sections;
4. emits a feature-local execution packet for the current feature.

### Rule of thumb

- `requirements.xml` changes only if business goal, scope, invariant, or failure policy changes.
- `technology.xml` changes only if runtime stack, external system, or verification toolchain changes.
- `development-plan.xml` changes when execution topology or module boundaries change.
- `knowledge-graph.xml` changes when module relations, interfaces, or flow links change.
- `verification-matrix.md` changes when a new verification lane, scenario, or gate is introduced.
- feature packet docs change for every substantial feature or wave.

## End-to-end lifecycle

### Step 0. Human idea
Input from the human Architect, e.g.:

> “We need nonstop agents, strict logging, module splitting, frontend visual review, and code size enforcement.”

### Step 1. Architect formalizes
Architect agent:
- creates a feature ID;
- writes feature brief;
- updates GRACE artifacts where necessary;
- writes impacted surfaces and verification expectations.

### Step 2. Planner slices
Planner agent:
- breaks the feature into waves;
- breaks waves into packets;
- assigns packet types: docs / backend / frontend / observability / tests / review;
- assigns model + reasoning policy.

### Step 3. Prefect executes packets
Prefect:
- picks ready packets by dependency order;
- launches the correct role prompt;
- persists packet state in files;
- retries allowed failures;
- routes rejected packets back into rework.

### Step 4. Coder implements
Coder agent receives:
- packet contract;
- write scope;
- acceptance criteria;
- verification profile;
- reasoning level.

### Step 5. Verifier validates
Verifier:
- runs packet-specific tests;
- reviews logs/traces/digests;
- records evidence;
- emits observability verdict.

### Step 6. Reviewer judges
Reviewer:
- reads implementation summary;
- reads verification summary;
- returns packet-level technical acceptance or rejection.

### Step 7. Architect accepts the wave
Architect gate:
- reads reviewer and verifier outputs;
- checks business fit, UX fit, and visual frontend proof;
- accepts or rejects the wave.

### Step 8. Prefect routes next action
If reviewer accepts and architect accepts:
- mark wave accepted and unblock the next wave.

If rejected with rework:
- Prefect creates a rework packet from the reviewer blocker.

If blocked by architecture:
- Prefect escalates to the human Architect queue.

## Who launches the Architect?

Phase 1 recommendation:
- **You** start a feature explicitly.
- Prefect runs the Architect flow from that feature request.

So the trigger is human-owned, orchestration is Prefect-owned.

Later, phase 2 can add scheduled backlog grooming or auto-follow-up flows, but initial feature creation should stay human-triggered.

## How does the Architect agent know where to write?

Through three layers:

1. project GRACE baseline in repo root;
2. feature packet templates and role contracts;
3. explicit prompt instructions that tell it to patch existing artifacts incrementally.

That means the intelligence lives in:
- prompt contracts;
- file templates;
- repository conventions.

Not in Prefect itself.

Prefect is the orchestrator, not the semantic planner.

## Monitoring and manageability in Prefect

Prefect already gives useful built-ins:
- flow run history;
- task run history;
- retries and failure states;
- run logs;
- manual rerun/restart;
- deployment scheduling;
- concurrency limits;
- work pools / workers;
- state transitions visible in UI.

What Prefect does **not** know by itself:
- GRACE acceptance semantics;
- whether a packet is truly architecturally acceptable;
- whether observability evidence is sufficient.

That logic stays in our role contracts and packet state files.

## What happens when Reviewer rejects?

Reviewer writes packet blocker reasons into the packet review result.
Then Prefect does one of two things:

### Rework path
If blocker is localized and remediable:
- Prefect creates a child rework packet;
- child packet references parent packet;
- coder gets the blocker context;
- reviewer re-checks after verifier reruns.

### Architect escalation path
If blocker means wrong decomposition, wrong architecture, or unclear business intent:
- Prefect creates an architect decision item;
- human Architect or Architect agent updates artifacts;
- planner may re-slice packets.

Architect performs the final wave gate. Visual frontend proof belongs to that architect wave review, with reviewer/verifier evidence as input.
So the reviewer does not create the packet manually.
The orchestration layer creates it from reviewer or architect output.

## Reasoning policy

You asked for different reasoning levels. Recommended initial policy:

- Architect agent: `xhigh`
- Planner agent: `xhigh`
- Reviewer agent: `high` or `xhigh`
- Verifier agent: `medium` or `high`
- Coder packet types:
  - docs-only / prompts-only: `medium`
  - bounded refactor: `high`
  - core workflow refactor: `xhigh`
  - test adaptation: `medium`
  - UI polish with strict constraints: `high`

Routing and round-robin stay inside cliproxy behind the `codexN` wrapper.
Prefect should launch one configured wrapper such as `codex1`, pass plain model `gpt-5.4`, and request role + reasoning.
Prefect should not rotate `CODEX_HOME` directories itself and should not use profile-prefixed model names.

## Frontend visual proof

Visual verification must be explicit at artifact stage.

Every frontend-touching feature should define in its packet bundle:
- target surfaces;
- expected UI states;
- required E2E file(s);
- screenshot or visual proof expectation;
- fallback/empty/error expectations;
- observability checks after E2E.

This should be added during feature formalization, not as an afterthought.

## Minimal phase-1 file-backed state

Recommended state files:

- `prefect_grace/state/features.yaml`
- `prefect_grace/state/packets.yaml`
- `prefect_grace/state/reviews.yaml`
- `prefect_grace/state/wave_reviews.yaml`
- `prefect_grace/state/decisions.yaml`
- `prefect_grace/state/runs/`

This is enough to start.

## First implementation waves

### Wave 1
Foundations only.
- role contracts
- prompt templates
- packet templates
- file-backed state
- Prefect scaffold
- feature bootstrap command

### Wave 2
Execution loop.
- architect flow
- planner flow
- coder packet flow
- reviewer flow
- rework packet generation

### Wave 3
Verification rigor.
- backend quick profile integration
- frontend Playwright profile integration
- post-test observability gate integration
- evidence bundling

### Wave 4
Non-stop operation.
- queue polling
- concurrency controls
- stuck packet detection
- escalation flow
- dashboards / summaries
