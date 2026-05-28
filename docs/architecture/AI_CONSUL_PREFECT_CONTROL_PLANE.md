# AI Consul Prefect Control Plane

Status: proposal
Date: 2026-05-28
Scope: design note for a controlled multi-agent consultation workflow

## Problem

The current Council-style tools are too heavy for GRACE planning and review work.
They tend to mix the useful part, which is independent multi-agent reasoning, with
unwanted mechanics: git worktrees, branch merges, autonomous rounds, plan files,
and opaque consensus synthesis.

For GRACE Canon design work we need a smaller and more controllable workflow:

- discuss a TZ or architecture packet from several viewpoints;
- ask clarifying questions over several human-controlled rounds;
- decide what is useful for MVP and what must stay out of scope;
- unblock stuck orchestrator features by running targeted triage;
- run deeper review workflows without giving agents write access to the repo;
- preserve all evidence as traceable artifacts.

Prefect should be the control plane. The AI Consul layer should be a deterministic
execution adapter and consensus protocol, not a competing daemon.

## Core Idea

AI Consul is a reusable Prefect-backed consultation workflow:

```text
case input
  -> build context
  -> run independent agents in parallel
  -> normalize findings
  -> score consensus deterministically
  -> synthesize a readable report
  -> wait for human decision / next round
```

The agents may be Codex, Gemini, Claude, or other providers later. The control
plane is still Prefect: retries, timeouts, logs, state, run history, artifacts,
manual reruns, and scheduling live there.

The agents do not own orchestration. They only produce bounded review outputs.

## Design Principles

- Human-controlled rounds. The system should not decide to start extra debate
  rounds by itself.
- No git mutation by default. Review agents must not create branches, commits, or
  merges for planning/review cases.
- Specializations are configuration, not new orchestration code.
- Consensus must be auditable. A final summary is not enough; it must show which
  agents supported each item and why it was accepted, deferred, or rejected.
- MVP bias. The protocol should explicitly reject large additions, live execution,
  dashboard work, or infrastructure expansion unless the specialization asks for
  it.
- Artifacts first. Every run should produce stable files that can be attached to
  packets and Prefect artifacts.

## Specialization Packs

A specialization defines the task shape, roles, output schema, and consensus
policy. Examples:

```yaml
name: grace_tz_mvp_review
purpose: Review a TZ and decide what small useful additions fit MVP.
agents:
  - id: architect
    engine: gemini
    focus: system boundaries, portability, install/runtime contracts
  - id: pragmatist
    engine: codex
    focus: smallest useful implementation path, testability, effort
  - id: critical_reviewer
    engine: claude
    focus: blockers, safety gates, ambiguity, non-goals
output_schema:
  - requirements
  - clarifying_questions
  - recommendations
  - risks
  - do_not_add_for_mvp
  - verdict
consensus_policy:
  accepted_if: support_count >= 2 and effort in [S, M] and not expands_scope
  must_if: support_count >= 2 and max_risk in [high, critical]
  rejected_if: effort == L or expands_scope or requires_live_execution
round_policy:
  mode: human_controlled
```

Other likely packs:

- `blocked_feature_triage`: inspect a stuck packet, failures, evidence, and
  propose the smallest unblock path.
- `review_gate`: run architecture/correctness/ops review before accepting a
  non-trivial change.
- `mvp_scope_gate`: classify a proposal into must/should/defer/reject for MVP.
- `rework_plan`: turn reviewer findings into a small ordered rework plan.

## Prefect Flow Shape

```text
ai_consul_case_flow
  build_case_context_task
  run_agent_review_task[codex]
  run_agent_review_task[gemini]
  run_agent_review_task[claude]
  normalize_agent_outputs_task
  score_consensus_task
  synthesize_consensus_report_task
  publish_consul_artifacts_task
```

For human-controlled continuation:

```text
ai_consul_next_round_flow
  load_previous_case_task
  add_human_notes_task
  build_round_context_task
  run_agents_parallel
  normalize_and_score
  publish_round_artifacts
```

## Consensus Protocol

Each agent should answer in a strict, parseable format:

```markdown
# Verdict
GO | CONDITIONAL_GO | NO_GO

# Recommendations
| id | title | priority | effort | expands_scope | rationale | acceptance_criteria |
|---|---|---|---|---|---|---|

# Risks
| id | severity | risk | mitigation |
|---|---|---|---|

# Clarifying Questions
- ...

# Do Not Add For MVP
- ...
```

The normalizer converts agent outputs into canonical JSON:

```json
{
  "agent": "codex",
  "verdict": "CONDITIONAL_GO",
  "items": [
    {
      "id": "MVP-RESULT-MANIFEST",
      "title": "Result manifest",
      "priority": "P1",
      "effort": "S",
      "expands_scope": false,
      "risk_refs": ["R-REPRODUCIBILITY"],
      "confidence": 0.86
    }
  ]
}
```

The scorer should be deterministic:

```text
ACCEPTED:
  support_count >= 2
  and effort in S/M
  and expands_scope == false

MUST:
  support_count >= 2
  and max_risk >= high

SHOULD:
  support_count >= 2
  and max_risk < high

DISPUTED:
  support_count == 1
  or agents materially disagree

REJECTED_FOR_MVP:
  effort == L
  or expands_scope == true
  or requires live execution / GUI / large infrastructure
```

An LLM may write the final prose, but it must write from the computed table. A
validator should check that `consensus.md` does not claim acceptance for items
that the scorer marked disputed or rejected.

## Artifacts

Every case should produce a stable artifact directory:

```text
.ai-consul/runs/<case_id>/
  case.yaml
  input/
    prompt.md
    files_manifest.json
    context.md
  rounds/
    001/
      agents/
        codex.md
        gemini.md
        claude.md
      normalized/
        codex.json
        gemini.json
        claude.json
      consensus_table.json
      consensus.md
      stderr/
        codex.err
        gemini.err
        claude.err
  meta.json
```

Prefect artifacts should link to:

- `consensus.md`;
- `consensus_table.json`;
- individual agent responses;
- source file manifest and hashes.

## MVP Candidate

Start with one specialization: `grace_tz_mvp_review`.

MVP behavior:

1. Accept `prompt`, `files`, `cwd`, `out_dir`, `specialization`.
2. Build `context.md` from the prompt and selected files.
3. Run Codex, Gemini, and Claude in parallel with hard timeouts.
4. Save stdout/stderr separately.
5. Parse strict markdown sections into normalized JSON.
6. Compute consensus table deterministically.
7. Generate `consensus.md` from the computed table.
8. Publish Prefect artifacts.
9. Support manual next round with human notes.

Initial CLI wrapper:

```bash
python -m prefect_grace.ai_consul run \
  --cwd /opt/astro-project \
  --specialization grace_tz_mvp_review \
  --prompt prompt.md \
  --file docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md \
  --file prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/EXECUTION_PACKET.md
```

## Non-Goals For MVP

- No autonomous git branch creation.
- No automatic merge, push, or worktree cleanup.
- No live agent execution against product code.
- No dashboard beyond Prefect artifacts.
- No multi-tenant permission model.
- No marketplace or plugin system.
- No automatic extra debate rounds unless a human starts the next round.

## Open Questions

- Should synthesis default to Claude, Codex, or a configurable model?
- Should the scorer require `support_count >= 2` or allow one high-confidence
  critical blocker to become `MUST_REVIEW`?
- How strict should the first parser be: markdown tables only, or JSON fenced
  blocks inside markdown?
- Should `.ai-consul/runs` be committed for architecture decisions, or treated as
  runtime evidence copied into packet artifacts?
- Which GRACE packet status should represent "human clarification required"?
