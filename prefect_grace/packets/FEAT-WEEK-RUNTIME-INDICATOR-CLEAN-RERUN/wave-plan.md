# Wave Plan: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN

## Objective
Expandable dev indicator on Week screen clean rerun

## Waves
1. W01 — Week Helper Rerun Evidence Closeout: Re-run the bounded Week runtime diagnostics disclosure and close targeted frontend plus packet-local read-only evidence without canonical Today/Week ownership.

## Packet Registry
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` — role `coder` — Week Dev Indicator Diagnostics Disclosure
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` depends on FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING, FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE` depends on FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT` depends on FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE, FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE
- `FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-ARCHITECT-WAVE-GATE` depends on FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT

## Exit Conditions
- Week dev indicator implementation remains within architect allowed write scope.
- Targeted unit, Playwright behavior, Playwright visual, and packet-local read-only observability checks pass or produce an accepted degraded-but-expected observability verdict.
- Visual evidence proves dev-collapsed, dev-expanded, and prod-unchanged Week states.
- Reviewer accepts the coder packet against scope, behavior, verification evidence, and frozen-scope constraints.
- Architect wave gate accepts or blocks the wave with a concrete verdict.
