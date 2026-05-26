# Execution Packet: GRACE Evidence Contracts MVP

## Objective

Implement a typed evidence and verifier contract layer for the portable GRACE
orchestrator so packet acceptance no longer depends on vague Markdown evidence
requests or unchecked LLM file references.

The goal is not to replace the verifier with a script. The verifier remains an
agent that can run commands, inspect logs, open UI, reason about results, and
summarize evidence. The platform must add the deterministic contract layer
around that agent:

- what evidence is required;
- who owns producing it;
- when it is required (`packet_local` vs `wave_final`);
- whether it is possible inside the packet scope;
- what artifact paths were claimed;
- whether those artifacts actually exist;
- how blockers are routed when evidence is missing, invalid, deferred, or out
  of scope.

This packet must not implement live agent execution, worktree management,
merge steward, or product backend/frontend changes. It is a platform contract
and validation packet.

## Slice

- slice_id: `SLICE-GRACE-EVIDENCE-CONTRACTS-MVP`
- slice_slug: `grace-evidence-contracts-mvp`
- feature_id: `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP`
- packet_id: `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP-W01-PACKET-ARTIFACT-LAYOUT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/verification_profile.py`
- `/opt/astro-project/prefect_grace/policies/verification.yaml`
- `/opt/astro-project/prefect_grace/prompts/verifier_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/reviewer_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/architect_prompt.md`

## Impacted Modules

- `M-GRACE-EVIDENCE-CONTRACTS`
- `M-GRACE-VERIFIER-CONTRACT`
- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-ARTIFACT-VALIDATOR`
- `M-GRACE-BLOCKER-ROUTING`
- `M-GRACE-CLI`
- `M-GRACE-PROMPTS`

## Required Design Decisions

### 1. Verifier Remains An Agent

Do not turn verification into a purely scripted gate. The verifier is a model
agent with `medium` reasoning by default. It may run tests, inspect logs, open
UI, compare screenshots, and summarize evidence.

The deterministic platform layer validates only the contract and artifacts:

- evidence requirement schema;
- stage/owner/producer/profile consistency;
- claimed artifact existence;
- manifest shape;
- blocker category and routing.

### 2. Evidence Requirements Are Typed

Evidence must not be a vague free-form sentence such as "attach logs". Every
requirement must have at least:

- `id`;
- `kind`;
- `stage`;
- `owner`;
- `producer`;
- `profile` or explicit instruction;
- `required` flag;
- `coder_blocking` flag;
- `artifact_patterns` or `expected_artifacts`.

### 3. Packet-local And Wave-final Are Separate

`packet_local` evidence can block the packet if it is required and feasible in
the packet scope. `wave_final` evidence must not block individual coder packets
unless the packet itself is the wave-final verifier packet.

If a packet-local verifier cannot produce a requested wave-final artifact, the
result must be `deferred`, not `coder_failed`.

### 4. Evidence Contract Invalid Routes To Architect

If the architect/planner requests impossible, out-of-scope, unowned, or
unprofiled evidence, the coder must not be re-run. The blocker category must be
`evidence_contract_invalid` and route to architect/planner contract rework.

### 5. Artifact References Must Be Verified

LLM output is not trusted as artifact existence proof. If verifier claims an
artifact path, the platform must verify the file exists under allowed artifact
roots or mark it `artifact_reference_invalid`.

### 6. Avoid Configuration Sprawl

The project already has many knobs. Do not add a large new config system.
Preferred order:

1. Parse evidence requirements from packet sections where possible.
2. Reuse `prefect_grace/policies/verification.yaml` profiles.
3. Add compact Python dataclasses/schemas inside `prefect_grace/platform`.
4. Add a small policy file only if tests prove packet-local schema is not
   enough.

### 7. Existing Roles Stay

Do not create a new heavy role for this packet. Use existing roles:

- `context_scout` is pre-architect and out of scope here;
- `architect` writes evidence requirements;
- `coder` may run self-checks but is not the acceptance source of truth;
- `verifier` independently produces evidence manifest;
- `reviewer` judges verified manifest and implementation;
- deterministic platform validates manifest/artifact references.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/evidence_contract.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/platform/blocker_routing.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/verification_profile.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/policies/verification.yaml`
- `/opt/astro-project/prefect_grace/prompts/verifier_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/reviewer_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/architect_prompt.md`
- `/opt/astro-project/scripts/grace_lint.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_evidence_contract.py`
- `/opt/astro-project/tests/test_prefect_grace_evidence_manifest.py`
- `/opt/astro-project/tests/test_prefect_grace_artifact_validator.py`
- `/opt/astro-project/tests/test_prefect_grace_blocker_routing.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_parser.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/telegram_notify.py`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing MVP-1 and MVP-2 platform tests continue to pass.
- Existing CLI command JSON envelope remains stable: `ok`, `project_key`,
  `command`, `result`, `data`, `warnings`, `errors`.
- No product backend/frontend files are modified.
- No live agents are started in tests.
- No real Prefect flow runs are created in tests.
- No source packet markdown is mutated by validation commands.
- Runtime/review evidence is written under `EVIDENCE/`, `REVIEWS/`,
  `REWORK/`, and `SUMMARY.md` according to packet artifact layout rules.
- No secrets or raw env values are printed in errors, manifests, or artifacts.
- Verifier prompt remains clear that verifier may run checks and inspect logs,
  but must return structured evidence manifest data.

## GRACE Canon Script Discipline

Every new Python module under `/opt/astro-project/prefect_grace/platform/**`
must keep strict GRACE-addressable structure:

- `AI_HEADER` banner in the first 30 lines.
- `START_MODULE_CONTRACT` / `END_MODULE_CONTRACT`.
- `START_MODULE_MAP` / `END_MODULE_MAP`.
- Paired `START_BLOCK` / `END_BLOCK` for semantic blocks.
- `START_FUNCTION_CONTRACT` / `END_FUNCTION_CONTRACT` for every public
  function or public method.
- No Prefect imports in evidence contract, manifest, artifact validator, or
  blocker routing modules.

## Required Implementation Shape

### Evidence Requirement Schema

Add a typed model, for example:

```python
class EvidenceRequirement:
    id: str
    kind: str
    stage: str
    owner: str
    producer: str
    profile: str | None
    instruction: str
    required: bool
    coder_blocking: bool
    artifact_patterns: list[str]
```

Allowed values:

- `kind`: `test`, `visual`, `observability`, `diff`, `contract`,
  `human_signoff`, `runtime_log`;
- `stage`: `packet_local`, `wave_final`, `release_final`;
- `owner`: `coder`, `verifier`, `reviewer`, `architect`, `pipeline`;
- `producer`: `agent`, `pytest`, `playwright`, `cli`, `log_watch`,
  `post_test_review`, `manual`, `pipeline`.

### Evidence Contract Parser

Parse evidence requirements from a packet section such as:

```markdown
## Evidence Requirements

- id: EV-UI-WEEK-DEV-EXPANDED
  kind: visual
  stage: packet_local
  owner: verifier
  producer: playwright
  profile: frontend_quick
  required: true
  coder_blocking: false
  artifact_patterns:
    - screenshots/week-dev-expanded.png
```

MVP may support YAML fenced blocks or strict bullet/YAML blocks, but parsing
must be deterministic and tested. If the packet has no evidence requirements,
return an empty contract with a warning, not a hidden default.

### Evidence Contract Validation

Add validation that catches:

- missing `id`;
- duplicate ids;
- unknown `kind`, `stage`, `owner`, or `producer`;
- required evidence without owner;
- required evidence without producer;
- profile reference that does not exist in `verification.yaml`;
- `packet_local` evidence marked required but impossible under declared owner;
- `wave_final` evidence marked `coder_blocking=true`;
- artifact pattern missing for required non-human evidence.

Validation result must be structured:

```json
{
  "ok": false,
  "errors": [
    {
      "code": "evidence_contract_invalid",
      "evidence_id": "EV-OBS-WEEK",
      "route_to": "architect",
      "message": "wave_final evidence cannot be coder_blocking"
    }
  ],
  "warnings": []
}
```

### Evidence Manifest

Add a typed manifest model for verifier output:

```json
{
  "packet_id": "...",
  "generated_by": "verifier",
  "evidence": [
    {
      "id": "EV-UI-WEEK-DEV-EXPANDED",
      "status": "collected",
      "stage": "packet_local",
      "producer": "playwright",
      "artifact_paths": ["..."],
      "summary": "..."
    }
  ],
  "blockers": []
}
```

Allowed evidence statuses:

- `collected`;
- `missing`;
- `deferred`;
- `not_applicable`;
- `failed`;
- `artifact_reference_invalid`;
- `contract_invalid`.

### Artifact Validator

Add deterministic validation for verifier-claimed artifacts:

- path must be relative or under allowed artifact roots;
- path must exist if status is `collected`;
- file size/hash metadata should be recorded when available;
- missing file converts evidence status to `artifact_reference_invalid`;
- invalid artifact reference routes to verifier/pipeline, not coder.

### Blocker Routing

Add routing rules:

```text
implementation_failed        -> coder
verification_failed          -> coder if caused by implementation test failure
failed_verification          -> coder if command failure is implementation-owned
evidence_contract_invalid    -> architect
missing_verification_profile -> architect/planner
artifact_reference_invalid   -> verifier/pipeline
evidence_not_generated       -> verifier/pipeline
environment_blocker          -> infra/operator
scope_violation              -> architect decision
wave_final_evidence_pending  -> not packet-blocking
review_rework_required       -> coder/reviewer route
```

Expose a pure function, for example:

```python
def route_evidence_blocker(error: dict) -> dict:
    ...
```

### CLI

Add CLI commands without running live agents:

- `validate-evidence-contract <packet_path> --json`
- `validate-evidence-manifest <manifest_path> --packet <packet_path> --artifact-root <path> --json`

Both must use the stable JSON envelope.

### Prompt Updates

Update prompts only to clarify contracts:

- `architect_prompt.md`: architect must assign evidence `owner`, `stage`,
  `producer`, `profile`, and `coder_blocking`.
- `verifier_prompt.md`: verifier independently runs checks, inspects logs/UI,
  returns evidence manifest, and distinguishes impossible/deferred evidence
  from implementation failure.
- `reviewer_prompt.md`: reviewer consumes verified manifest and must not route
  evidence contract failures to coder.

Do not rewrite prompts wholesale.

## Verification

Run these commands from `/opt/astro-project`:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_evidence_contract.py \
  tests/test_prefect_grace_evidence_manifest.py \
  tests/test_prefect_grace_artifact_validator.py \
  tests/test_prefect_grace_blocker_routing.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_packet_parser.py
```

Run MVP regression tests:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_dag.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_runtime_adapter.py
```

Run compile check:

```bash
python3 -m compileall -q prefect_grace
```

Run strict GRACE marker lint:

```bash
python3 scripts/grace_lint.py prefect_grace/platform
```

Run CLI smoke checks:

```bash
python3 -m prefect_grace.cli validate-evidence-contract \
  prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md \
  --json

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md \
  --strict \
  --json
```

## Expected Evidence

Attach under `## Evidence`:

- `git diff --stat`.
- Full list of changed files.
- Output of new evidence contract tests.
- Output of MVP regression tests.
- Output of compile check.
- Output of `python3 scripts/grace_lint.py prefect_grace/platform`.
- JSON output of CLI smoke checks.
- Example valid evidence contract parsed from this packet or a fixture.
- Example invalid contract showing route to architect.
- Example manifest with a missing artifact showing route to verifier/pipeline.
- Explicit note that no live agents or Prefect runs were started.
- Explicit note that no product backend/frontend files changed.

## Escalation Triggers

Stop and ask Controller if:

- implementing this requires live verifier agent execution;
- implementing this requires changing product backend/frontend code;
- implementing this requires changing Codex/Claude/agy launcher behavior;
- evidence schema cannot be parsed deterministically from packet markdown;
- a new broad config system seems necessary;
- prompt changes become a rewrite rather than a minimal contract clarification;
- tests require real browser, real Prefect, or real external logs.

## Reviewer Gate

Reviewer must reject if:

- verifier evidence is accepted from plain prose without a manifest;
- nonexistent artifact paths pass validation;
- `wave_final` evidence blocks a packet-local coder by default;
- evidence contract invalid routes to coder instead of architect;
- artifact reference invalid routes to coder instead of verifier/pipeline;
- CLI JSON output is not parseable or lacks stable envelope fields;
- new modules fail GRACE marker lint;
- live agents or real Prefect runs start during tests;
- product backend/frontend files appear in the diff.

## Evidence

Worker fills this section.

## Reviewer Notes

Reviewer fills this section.
