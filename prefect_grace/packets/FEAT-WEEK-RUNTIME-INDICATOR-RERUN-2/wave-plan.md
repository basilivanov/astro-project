# Wave Plan: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2

## Objective
Expandable dev indicator on Week screen rerun 2

## Waves
1. W01 — Week runtime indicator rerun implementation and closeout: Re-run the bounded Week runtime indicator implementation and evidence lane without widening the approved Week helper-state slice.

## Packet Registry
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` — role `coder` — Week Dev Indicator Diagnostics Disclosure
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` depends on FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-PLANNER-SLICING
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE` depends on FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT` depends on FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE, FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE
- `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-ARCHITECT-WAVE-GATE` depends on FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT, FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE

## Exit Conditions
- The coder packet completes within the approved Week runtime indicator slice and preserves all frozen-scope boundaries.
- The verifier packet records passing Week unit, behavior, and visual lanes plus a FLOW-TODAY-WEEK-WEEK verdict of clean or degraded-but-expected.
- The reviewer packet accepts the coder output and explicitly confirms the Week top area remains local and not banner-like.
- The architect wave gate accepts the wave with no unresolved scope drift, evidence gap, or observability blocker.
