# Packet: FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-REVIEWER-VERDICT

## Summary
Judge the packet outcome and decide accepted, rework_required, blocked, or escalate_to_architect.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE

## Acceptance Criteria
- Exactly one verdict is returned.
- Blockers are actionable.
- Follow-up action is explicit.
- Scope containment, UI behavior, production inertness, visual evidence, and observability evidence are each checked explicitly.

## Verification Profile
- backend: not required
- frontend: consume verifier screenshots, Playwright evidence, and unit-test evidence.
- observability: consume verifier Today post-test verdict and notes.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Do not invent new scope.
- Do not accept missing evidence.
- Do not accept if the disclosure exposes any visible field beyond render path, bootstrap result, and current mode.
- Do not accept if visual proof is missing for the dev-expanded state or if production inertness is not proven.
- Do not accept `no-evidence-blocker` or `unexpected-degradation` as a completed observability gate.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE

## Notes
- Escalate to architect when the blocker changes decomposition or business semantics.
- Treat missing Prefect/evidence artifacts as a pipeline blocker, not a reason to infer acceptance from green tests alone.
