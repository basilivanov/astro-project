# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY

## Summary
Constrain the existing shell-owned DEV/PROD badge so only `/` in non-production can act as the Day disclosure entry point, while production and non-Day routes remain inert.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx

## Inputs
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/EXECUTION_PACKET.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/requirements.slice.expandable-day-screen-dev-indicator.xml

## Acceptance Criteria
- The existing compact chip remains shell-owned and visually compact in collapsed state.
- Interactive behavior is exposed only on `/` and only in non-production.
- Production and non-Day routes remain visually and behaviorally unchanged.
- No diagnostics body, banner, or broader shell surface is rendered from layout scope.

## Verification Profile
- backend: {'required_commands': [], 'evidence': ['No backend diff is permitted.'], 'verdict_expectation': 'not_required'}
- frontend: {'required_commands': [], 'visual_verification': {'status': 'deferred_to_FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-PLAYWRIGHT-VISUAL-COVERAGE', 'artifacts': ['Collapsed compact chip proof must be captured later on the Day route.']}, 'evidence': ['Verifier expects route gating to stay inside layout scope and not render disclosure content from the shell.'], 'verdict_expectation': 'deferred_until_downstream_ui_proof'}
- observability: {'required_commands': [], 'evidence': ['Today observability closeout is deferred to FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE.'], 'verdict_expectation': 'deferred'}

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to `/opt/astro-project/frontend/app/layout.tsx` and does not introduce behavior outside the Day route.
- Production inertness is preserved by implementation design and remains available for downstream unit proof.
- The packet leaves FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-DIAGNOSTICS-DISCLOSURE unblocked without widening the shell surface.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING

## Notes
- Escalate if the shell-owned badge cannot be route-gated to `/` without leaking interaction to other routes.
- Do not add any new runtime fields or backend traffic.
