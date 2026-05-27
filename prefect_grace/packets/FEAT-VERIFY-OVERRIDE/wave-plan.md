# Wave Plan: FEAT-VERIFY-OVERRIDE

## Objective
Verify override feature

## Waves
1. W01 — Wave: Test (required)

## Packet Registry
- `FEAT-VERIFY-OVERRIDE-W01-CODER` — role `coder` — Coder
- `FEAT-VERIFY-OVERRIDE-W01-VERIFIER` — role `verifier` — Verifier
- `FEAT-VERIFY-OVERRIDE-W01-REVIEWER` — role `reviewer` — Reviewer

## Dependency Rules
- `FEAT-VERIFY-OVERRIDE-W01-CODER` depends on FEAT-VERIFY-OVERRIDE-W00-PLANNER-SLICING
- `FEAT-VERIFY-OVERRIDE-W01-VERIFIER` depends on FEAT-VERIFY-OVERRIDE-W01-CODER
- `FEAT-VERIFY-OVERRIDE-W01-REVIEWER` depends on FEAT-VERIFY-OVERRIDE-W01-CODER, FEAT-VERIFY-OVERRIDE-W01-VERIFIER

## Exit Conditions
- All generated coder packets are implemented.
- Verifier evidence is recorded for the wave.
- Reviewer and architect gates are resolved.
