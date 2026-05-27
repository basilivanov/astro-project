# Packet: FEAT-DAY-DEV-INDICATOR-W01-LIVE-IMPLEMENTATION-PACKET

## Summary
Scope: Keep the existing day/home dev or prod chip visually compact and localized around the current indicator.; In dev mode, tapping the chip expands a small inline diagnostics panel.; {'Show only a short set of useful diagnostics fields': 'render path, bootstrap result, and current mode.'}; Reuse existing runtime or debug data already available on the frontend.; Keep the hero or top area visually quiet and avoid noticeable layout pollution.. Acceptance: In dev mode, tapping the existing dev indicator reveals a compact diagnostics panel.; The diagnostics panel shows render path, bootstrap result, and current mode only.; Tapping the indicator again collapses the panel.; In prod mode, the UI remains visually unchanged and the indicator does not reveal a diagnostics panel.; The change does not visibly pollute or displace the day hero or top area.. Non-goals: Do not change day business logic.; Do not change scoring, explainability, or payload contracts.; Do not request new backend fields.; Do not expose correlation, trace, or raw payload diagnostics in user-facing UI.; Do not change prod mode behavior.. Visual expectations: The indicator remains compact in both collapsed and expanded states.; The diagnostics panel looks like a small local reveal near the existing chip, not a banner.; Expanded dev diagnostics must not dominate the hero or top area..

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- FEAT-DAY-DEV-INDICATOR-W00-PLANNER-SLICING
- FEAT-DAY-DEV-INDICATOR-W00-ARCHITECT-FORMALIZATION
- feature brief

## Acceptance Criteria
- Requested code change is implemented within scope.
- Targeted tests are added or updated if needed.
- Implementation notes are left for verifier and reviewer.

## Verification Profile
- backend: backend:quick or targeted tests as required by the packet
- frontend: targeted Playwright run if the packet touches UI
- observability: post-test log, digest, and trace review

## Execution Hints
-

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-DAY-DEV-INDICATOR-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
