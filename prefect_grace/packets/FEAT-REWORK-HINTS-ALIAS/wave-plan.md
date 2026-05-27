# Wave Plan: FEAT-REWORK-HINTS-ALIAS

## Objective
Rework hints alias feature

## Waves
1. W01 — Implementation and acceptance wave: Implement, verify, review, and architect-accept the first bounded feature slice. (required)

## Packet Registry
- `FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION` — role `coder` — Implementation
- `FEAT-REWORK-HINTS-ALIAS-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-REWORK-HINTS-ALIAS-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION` depends on nothing
- `FEAT-REWORK-HINTS-ALIAS-W01-VERIFIER-EVIDENCE` depends on FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION
- `FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT` depends on FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION, FEAT-REWORK-HINTS-ALIAS-W01-VERIFIER-EVIDENCE
- `FEAT-REWORK-HINTS-ALIAS-W01-ARCHITECT-WAVE-GATE` depends on FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT

## Exit Conditions
- Coder packet is completed within scope.
- Verifier evidence is recorded.
- Reviewer technical gate is accepted or routed to rework.
- Architect wave gate accepts or blocks the wave.
