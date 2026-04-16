# FEAT-NOTIFY-CHECK W01 Binding Note

## Purpose

Record the exact repository bindings for the W01 coder packets before any Day Notify-check behavior work is attempted.

## Artifact Check

- `test -f /opt/astro-project/docs/notify-check-day-default-execute/architect_manifest.json` -> PASS
- `test -f /opt/astro-project/docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md` -> PASS
- `test -f /opt/astro-project/docs/notify-check-day-default-execute/EXECUTION_PACKET.md` -> PASS
- `rg -n --hidden -S "notify check|notify-check|notifyCheck|notify_check|execute=true|execute false" frontend/app frontend/components frontend/lib frontend/e2e` -> FAIL (exit 1, no matches)

## Concrete Day-Slice Bindings

- `M-FE-DAY-RUNTIME-INDICATOR`
  - `frontend/app/page.tsx`
  - `frontend/components/today/day-runtime-diagnostics-disclosure.tsx`
  - `frontend/components/today/daybrief-sections.tsx`
  - `frontend/test/app/home-page.test.tsx`
  - Why these belong: the Day home page renders the runtime badge/disclosure state, re-exports the Day disclosure surface, validates the Day disclosure behavior in Jest, and probes the same Day disclosure in Playwright.
- `e2e/<day-notify-check-spec>.spec.ts`
  - Concrete repo path available in allowed scope: `frontend/e2e/day-dev-indicator.spec.ts`
  - Binding limit: this file is only an adjacent Day runtime-indicator probe. It does not expose or verify a Day Notify-check intake/default/dispatch flow, so it cannot be treated as Notify-check acceptance evidence without a real Day Notify-check surface.

## Missing Day Notify-Check Bindings

- `M-FE-NOTIFY-CHECK-INTAKE-DEFAULTS`
  - Concrete binding found: none
  - Evidence: `rg -n --hidden -S "notify check|notify-check|notifyCheck|notify_check|execute=true|execute false" frontend/app frontend/components frontend/lib frontend/e2e` returned exit 1 with no Day-owned frontend match.
  - Scope implication: implementing this module would require inventing a new surface or widening beyond the currently bound Day runtime-indicator files.
- `M-FE-NOTIFY-CHECK-DISPATCH`
  - Concrete binding found: none
  - Evidence: the same frontend scan returned exit 1 with no Day-owned caller or dispatch path for a Notify-check flow.
  - Scope implication: there is no existing Day-owned dispatch file inside the bound frontend slice to edit.

## Frozen-Scope Check

- No binding in this scan requires editing `backend/**`, `prefect/**`, or `frontend/<non-day-slices>/**`.
- The repo does contain unrelated notify evidence outside the Day slice, but no Day-owned frontend Notify-check implementation path was found.

## Packet Verdict

- Verdict: `contract-mismatch-no-day-notify-surface`
- Reason: the current repo contains the Day runtime-indicator surface only; it does not contain a concrete Day Notify-check intake/default/dispatch surface inside the allowed write scope.

## Handoff Notes

- Downstream implementation packets must not infer Notify-check behavior from `frontend/e2e/day-dev-indicator.spec.ts`; that spec is runtime-indicator-only evidence.
- If architect intent remains unchanged, the next required step is reslicing or an explicit packet that first establishes a real Day Notify-check product surface.
- If architect intent is downgraded to the existing runtime-indicator surface only, downstream packets can use the concrete Day bindings above without further path discovery.
