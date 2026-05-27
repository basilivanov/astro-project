# Plan: Portable GRACE Orchestrator Review

## Context Check
- Repository history is non-empty; latest observed commit: `d3ec170 refactor(prefect-grace): split feature pipeline helpers`.
- Workspace top level was checked once as requested.
- No local `main` branch exists in this checkout; `master` is the available integration branch.
- This is a Round 1 planning-only artifact. No application, backend, frontend, or feature implementation code should be changed.

## Claim Status
- Claimed by: Codex.
- Partners: agent-Gemini, agent-Claude.
- Scope: review-only Council pass for the portable GRACE orchestrator specification and related execution packet.
- Status: planning complete for Round 1; execution/review still required.
- Verification profile: document-review evidence only. Backend/frontend tests are not required unless a later round changes executable code, which this task currently forbids.

## Task Checklist
- [ ] In the execution round, read the architecture source of truth:
  `docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`.
- [ ] Read the related packet:
  `prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/EXECUTION_PACKET.md`.
- [ ] Decide and justify the recommended product/project naming:
  - product/project name candidate: `GRACE Portable Orchestrator`;
  - architecture title: `Portable GRACE Orchestration Platform`;
  - package/repo name: `grace-orchestrator`.
- [ ] Identify must-fix issues before implementation, especially:
  - unclear MVP boundary, non-goals, and acceptance criteria;
  - unclear install/runtime boundary between portable package, host project, containers, Prefect, and local CLI;
  - missing public contracts for inputs, outputs, events, state transitions, config, secrets, and adapters;
  - portability assumptions tied to `/opt/astro-project`, Docker Compose service names, local paths, environment variables, or current GRACE internals;
  - idempotency, retries, duplicate execution, cancellation, resume, and partial-failure semantics;
  - ownership of orchestration state, migrations, cleanup, backup/restore, and audit trail;
  - auth, secrets handling, tenant/project isolation, and permission model;
  - observability requirements: structured logs, trace IDs, report/request IDs, replay/digest evidence, degradation signals;
  - operational controls: health checks, readiness, rollback, kill switch, quotas, cost limits, concurrency limits.
- [ ] Identify should-fix improvements, such as:
  - concise lifecycle or sequence diagram;
  - failure-mode matrix with expected fallback/degradation behavior;
  - explicit adapter/plugin contract for host applications;
  - sample minimal install and local smoke path;
  - compatibility/versioning policy for package, packet schema, and runtime;
  - UAT checklist and post-test evidence checklist.
- [ ] Produce a compact Council consensus artifact with:
  - final recommended name;
  - must-fix issues before implementation;
  - should-fix improvements;
  - go/no-go verdict;
  - short notes on any unresolved disagreements with partner agents.

## Phase Breakdown
- Phase 1: Evidence collection from the two source documents only.
- Phase 2: Name decision and terminology normalization.
- Phase 3: Architecture gap review focused on portability, contracts, install/runtime boundaries, and operations.
- Phase 4: Severity ranking into must-fix and should-fix buckets.
- Phase 5: Council reconciliation with agent-Gemini and agent-Claude outputs if available.
- Phase 6: Write a compact markdown review/consensus artifact in a clearly named review location, or update `plan.md` only if the Council workflow requires it.

## Round 1 Verdict
- Planning only: complete.
- Execution still needed: yes.
- Consensus vote for Round 1: NO.
