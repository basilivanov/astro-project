# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-ADD-TARGETED-PLAYWRIGHT-AND-VISUAL-EVIDENCE

## Summary
Add the dedicated Playwright coverage and runtime-indicator visual evidence required to prove dev-expanded and prod-unchanged behavior on the Day route.

## Wave
W01

## Role
coder

## Reasoning
medium

## Write Scope
- /opt/astro-project/frontend/e2e/day-dev-indicator.spec.ts
- /opt/astro-project/frontend/e2e/day-canon-visual-evidence.spec.ts

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W01-RENDER-DAY-LOCAL-DIAGNOSTICS-DISCLOSURE
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md

## Acceptance Criteria
- Dedicated Playwright coverage proves expand and collapse behavior for the dev indicator on `/` in the active dev stack.
- Visual evidence captures the compact collapsed state and expanded disclosure state without banner-like dominance.
- Production-unchanged proof is captured through the runtime-indicator visual lane or explicitly documented as an `E2E_PROD_BASE_URL` limitation paired with deterministic unit proof.
- Selectors and assertions remain scoped to the Day route and do not widen to other product surfaces.

## Verification Profile
- backend: {'required_commands': [], 'evidence': ['No backend diff is permitted.'], 'verdict_expectation': 'not_required'}
- frontend: {'required_commands': ['./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts', './scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"'], 'visual_verification': {'status': 'required_now', 'artifacts': ['Dev-collapsed screenshot', 'Dev-expanded screenshot', 'Production-unchanged screenshot or explicit production-host limitation note paired with unit proof']}, 'evidence': ['Playwright evidence must be attached with exact commands and PASS or FAIL outcomes.', 'Visual evidence must show the disclosure stays local to the chip area and does not visually dominate the hero.'], 'verdict_expectation': 'pass'}
- observability: {'required_commands': [], 'evidence': ['Today observability review is deferred to FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE after these runs.'], 'verdict_expectation': 'deferred'}

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Both targeted Playwright commands are recorded and produce deterministic evidence or an explicit documented blocker.
- Visual evidence includes collapsed and expanded dev states plus production-unchanged proof or the approved limitation fallback.
- No test helper or selector change leaks interaction beyond the Day route.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-RENDER-DAY-LOCAL-DIAGNOSTICS-DISCLOSURE

## Notes
- Frontend visual verification is mandatory because the packet touches UI proof.
- If a dedicated production host is unavailable, document the limitation explicitly instead of guessing.
